"""Manage only NetSentinel's narrowly identified Windows Firewall rules.

The broker must resolve app_id from its own observed-process inventory before
calling block. Browser callers never supply executable paths. Applying a rule
does not verify traffic blocking, which requires an independent controlled test.
"""
from __future__ import annotations

import hashlib
import ntpath
import os
from pathlib import Path, PureWindowsPath
import re
import threading

from .windows_security import NativeOperationError, PowerShellRunner


RULE_GROUP = "NetSentinel.Companion.v1"
APP_ID = re.compile(r"[0-9a-f]{64}\Z")


def validate_app_id(app_id: str) -> str:
    if not isinstance(app_id, str) or not APP_ID.fullmatch(app_id):
        raise ValueError("Application identity must be a lowercase SHA-256 digest")
    return app_id


def canonical_executable(executable: str) -> str:
    """Reject paths unsuitable for a local application firewall rule."""
    if not isinstance(executable, str) or not 4 <= len(executable) <= 1024:
        raise ValueError("Invalid executable path")
    path = PureWindowsPath(executable)
    if (not path.is_absolute() or len(path.drive) != 2 or path.drive[1] != ":"
            or path.suffix.lower() != ".exe" or any(ord(char) < 32 for char in executable)
            or any(char in executable for char in '*?<>"|') or ":" in executable[2:]
            or any(part in ("..", ".") or part.endswith((" ", ".")) for part in path.parts)):
        raise ValueError("Only a canonical local executable path is permitted")
    normalized = ntpath.normcase(ntpath.normpath(executable))
    if os.name != "nt":
        raise NativeOperationError("unsupported")
    try:
        actual = Path(executable).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("The executable is unavailable") from exc
    if not actual.is_file() or ntpath.normcase(str(actual)) != normalized:
        raise ValueError("The executable must be a canonical existing local file")
    return normalized


FIREWALL_SCRIPT = r"""
$group = 'NetSentinel.Companion.v1'
$description = 'NetSentinel owned application block v1'
$created = New-Object System.Collections.Generic.List[string]
$rollbackFailed = New-Object System.Collections.Generic.List[string]
$removed = New-Object System.Collections.Generic.List[string]
function Is-Owned($rule) {
  return ($rule.Group -ceq $group -and $rule.Description -ceq $description -and
    $rule.Name -cmatch '^NetSentinel\.Companion\.v1\.[0-9a-f]{64}\.(in|out)$')
}
function Named-Rule($name) {
  try { $found = @(NetSecurity\Get-NetFirewallRule -PolicyStore PersistentStore -Name $name -ErrorAction Stop) }
  catch { if ($_.CategoryInfo.Category -eq 'ObjectNotFound') { return $null }; throw }
  if ($found.Count -gt 1) { throw 'ownership_conflict' }
  if ($found.Count -eq 1) { return $found[0] }
  return $null
}
function Remove-Owned($name) {
  $rule = Named-Rule $name
  if ($null -ne $rule) {
    if (-not (Is-Owned $rule)) { throw 'ownership_conflict' }
    $rule | NetSecurity\Remove-NetFirewallRule -ErrorAction Stop
  }
}
try {
  $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
  Import-Module (Join-Path $PSHOME 'Modules\NetSecurity\NetSecurity.psd1') -ErrorAction Stop
  if ($request.operation -in @('block', 'unblock')) {
    if ($request.app_id -cnotmatch '^[0-9a-f]{64}$') { throw 'invalid_request' }
    $names = @(($group + '.' + $request.app_id + '.in'), ($group + '.' + $request.app_id + '.out'))
  }
  if ($request.operation -eq 'block') {
    if ($request.executable -notmatch '^[a-zA-Z]:\\' -or $request.executable -notmatch '\.exe$' -or
        $request.executable -match '[\x00-\x1f*?<>"|]' -or $request.executable.Substring(2).Contains(':') -or
        -not (Test-Path -LiteralPath $request.executable -PathType Leaf)) { throw 'invalid_request' }
    for ($i = 0; $i -lt 2; $i++) {
      $rule = Named-Rule $names[$i]
      $direction = if ($i -eq 0) { 'Inbound' } else { 'Outbound' }
      if ($null -ne $rule) {
        if (-not (Is-Owned $rule) -or [string]$rule.Enabled -ne 'True' -or
            [string]$rule.Action -ne 'Block' -or [string]$rule.Direction -ne $direction -or
            [string]$rule.Profile -ne 'Any') { throw 'ownership_conflict' }
        $application = $rule | NetSecurity\Get-NetFirewallApplicationFilter -ErrorAction Stop
        if ($application.Program -ine $request.executable) { throw 'ownership_conflict' }
      }
    }
    for ($i = 0; $i -lt 2; $i++) {
      $direction = if ($i -eq 0) { 'Inbound' } else { 'Outbound' }
      if ($null -eq (Named-Rule $names[$i])) {
        $null = NetSecurity\New-NetFirewallRule -PolicyStore PersistentStore -Name $names[$i] -DisplayName $names[$i] -Description $description -Group $group -Direction $direction -Action Block -Enabled True -Profile Any -Program $request.executable -Protocol Any -ErrorAction Stop
        $created.Add($names[$i])
      }
    }
    @{ success = $true; state = 'applied_not_traffic_verified'; rule_names = $names } | ConvertTo-Json -Depth 4 -Compress
  } elseif ($request.operation -eq 'unblock') {
    foreach ($name in $names) { $rule = Named-Rule $name; if ($null -ne $rule -and -not (Is-Owned $rule)) { throw 'ownership_conflict' } }
    foreach ($name in $names) { Remove-Owned $name; $removed.Add($name) }
    @{ success = $true; state = 'removed'; removed = @($removed.ToArray()) } | ConvertTo-Json -Depth 4 -Compress
  } elseif ($request.operation -in @('rules', 'cleanup')) {
    $candidates = @(NetSecurity\Get-NetFirewallRule -PolicyStore PersistentStore -ErrorAction Stop | Where-Object { $_.Group -ceq $group } | Select-Object -First 2001)
    if ($candidates.Count -gt 2000) { throw 'rule_limit' }
    $conflicts = 0
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($rule in $candidates) {
      if (-not (Is-Owned $rule)) { $conflicts++; continue }
      if ($request.operation -eq 'cleanup') { Remove-Owned $rule.Name; $removed.Add($rule.Name) }
      else {
        $parts = $rule.Name.Split('.')
        $items.Add(@{ app_id = $parts[3]; direction = [string]$rule.Direction; enabled = [string]$rule.Enabled; action = [string]$rule.Action; name = $rule.Name })
      }
    }
    @{ success = ($conflicts -eq 0); state = $(if ($request.operation -eq 'cleanup') { 'removed' } else { 'observed_rules' }); error = $(if ($conflicts -gt 0) { 'ownership_conflict' } else { $null }); rules = @($items.ToArray()); removed = @($removed.ToArray()); ownership_conflicts = $conflicts } | ConvertTo-Json -Depth 4 -Compress
  } else { throw 'invalid_request' }
} catch {
  $errorCode = (Error-Code $_)
  if ($_.Exception.Message -in @('ownership_conflict', 'invalid_request', 'rule_limit')) { $errorCode = $_.Exception.Message }
  foreach ($name in $created) { try { Remove-Owned $name } catch { $rollbackFailed.Add($name) } }
  @{ success = $false; state = 'failed'; error = $errorCode; rollback_failed = @($rollbackFailed.ToArray()); removed = @($removed.ToArray()) } | ConvertTo-Json -Depth 4 -Compress
}
"""


class FirewallController:
    """No implicit elevation and no global firewall resets or settings changes."""
    def __init__(self, runner=None):
        self.runner = runner or PowerShellRunner()
        self._lock = threading.Lock()

    def _execute(self, operation: str, **values) -> dict:
        with self._lock:
            result = self.runner.run(FIREWALL_SCRIPT, {"operation": operation, **values}, timeout=30)
        if type(result.get("success")) is not bool:
            raise NativeOperationError("invalid_response")
        allowed_errors = {"permission_denied", "unavailable", "ownership_conflict", "invalid_request", "rule_limit"}
        response = {"success": result["success"], "state": result.get("state") if result.get("state") in
                    ("applied_not_traffic_verified", "removed", "observed_rules", "failed") else "unknown",
                    "traffic_blocking_verified": False, "source": "Windows Firewall PersistentStore", "provenance": "LIVE"}
        if not response["success"]:
            response["error"] = result.get("error") if result.get("error") in allowed_errors else "native_failed"
        for key in ("rule_names", "removed", "rollback_failed"):
            response[key] = [name for name in result.get(key, [])[:2000] if isinstance(name, str) and
                             re.fullmatch(r"NetSentinel\.Companion\.v1\.[0-9a-f]{64}\.(in|out)", name)] if isinstance(result.get(key), list) else []
        response["ownership_conflicts"] = result.get("ownership_conflicts", 0) if type(result.get("ownership_conflicts", 0)) is int else 0
        response["rules"] = []
        for row in result.get("rules", [])[:2000] if isinstance(result.get("rules"), list) else []:
            if not isinstance(row, dict) or not isinstance(row.get("app_id"), str) or not APP_ID.fullmatch(row["app_id"]):
                continue
            response["rules"].append({"app_id": row["app_id"],
                "direction": row.get("direction") if row.get("direction") in ("Inbound", "Outbound") else "Unknown",
                "enabled": {"True": True, "False": False}.get(str(row.get("enabled"))),
                "action": row.get("action") if row.get("action") in ("Block", "Allow") else "Unknown"})
        return response

    def block(self, executable: str, app_id: str) -> dict:
        validate_app_id(app_id)
        canonical = canonical_executable(executable)
        if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != app_id:
            raise ValueError("Application identity does not match its canonical executable")
        return self._execute("block", executable=canonical, app_id=app_id)

    def unblock(self, app_id: str) -> dict:
        return self._execute("unblock", app_id=validate_app_id(app_id))

    def cleanup(self) -> dict:
        """Remove only rules whose exact group, name and ownership marker match."""
        return self._execute("cleanup")

    def rules(self) -> dict:
        return self._execute("rules")
