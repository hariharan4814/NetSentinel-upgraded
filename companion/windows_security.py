"""Fixed Windows security interfaces; no arbitrary command or scan-path API.

NativeOperationError.code is safe to return to a local authenticated operator.
Do not expose native stderr: Windows errors can include personal file paths.
"""
from __future__ import annotations

import base64
import ctypes
import json
import os
from pathlib import Path
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


class NativeOperationError(RuntimeError):
    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or {
            "unsupported": "This operation requires supported Windows interfaces.",
            "unavailable": "The Windows interface is unavailable.",
            "permission_denied": "Windows denied this operation. Check operator permissions.",
            "timeout": "Windows did not return within the request limit; its operation may continue.",
            "output_limit": "The Windows response exceeded the permitted size.",
            "invalid_response": "Windows returned an unexpected response.",
            "native_failed": "The Windows operation failed; review Windows Security locally.",
            "scan_busy": "A scan request is already being tracked.",
            "scan_unavailable": "Defender is unavailable, disabled, passive, or in an unsupported mode.",
        }.get(code, "The Windows operation could not be completed."))


def system_directory() -> Path:
    """Ask Windows, not a caller-controlled SystemRoot or PATH environment."""
    if os.name != "nt":
        raise NativeOperationError("unsupported")
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
    if not length or length >= len(buffer):
        raise NativeOperationError("unavailable")
    return Path(buffer.value)


PS_PREFIX = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$WarningPreference = 'SilentlyContinue'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
function Error-Code($record) {
  if ($record.CategoryInfo.Category -eq 'PermissionDenied' -or
      $record.Exception.HResult -eq -2147024891) { return 'permission_denied' }
  return 'unavailable'
}
function Utc-Date($value) {
  if ($null -eq $value) { return $null }
  try { if ($value.Year -lt 2000) { return $null }; return $value.ToUniversalTime().ToString('o') }
  catch { return $null }
}
"""


class PowerShellRunner:
    """Bounded process runner used only with module-owned, fixed script constants."""
    MAX_OUTPUT = 131072

    def run(self, script: str, values: dict | None = None, *, timeout: float = 20) -> dict:
        payload = json.dumps(values or {}, ensure_ascii=True).encode("utf-8")
        if len(payload) > 8192 or not 0 < timeout <= 86400:
            raise ValueError("Invalid native request bounds")
        directory = system_directory()
        executable = directory / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if not executable.is_file():
            raise NativeOperationError("unavailable")
        command = base64.b64encode((PS_PREFIX + script).encode("utf-16-le")).decode("ascii")
        environment = os.environ.copy()
        environment["PSModulePath"] = str(executable.parent / "Modules")
        environment["SystemRoot"] = str(directory.parent)
        environment["WINDIR"] = str(directory.parent)
        environment["PATH"] = str(directory)
        try:
            process = subprocess.Popen(
                [str(executable), "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", command],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                cwd=str(directory), env=environment,
            )
        except PermissionError as exc:
            raise NativeOperationError("permission_denied") from exc
        except OSError as exc:
            raise NativeOperationError("unavailable") from exc
        output = bytearray()
        over_limit = threading.Event()

        def drain(stream: Any, retain: bool) -> None:
            size = 0
            try:
                while chunk := stream.read(4096):
                    size += len(chunk)
                    if size > self.MAX_OUTPUT:
                        over_limit.set()
                        process.kill()
                        break
                    if retain:
                        output.extend(chunk)
            except (OSError, ValueError):
                pass
            finally:
                stream.close()

        workers = [threading.Thread(target=drain, args=(process.stdout, True), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, False), daemon=True)]
        for worker in workers:
            worker.start()
        try:
            process.stdin.write(payload)
            process.stdin.close()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.wait(timeout=5)
                raise NativeOperationError("timeout") from exc
        except BrokenPipeError as exc:
            raise NativeOperationError("native_failed") from exc
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for worker in workers:
                worker.join(timeout=5)
        if over_limit.is_set():
            raise NativeOperationError("output_limit")
        if process.returncode:
            raise NativeOperationError("native_failed")
        try:
            result = json.loads(output.decode("utf-8-sig"))
        except (ValueError, UnicodeError) as exc:
            raise NativeOperationError("invalid_response") from exc
        if not isinstance(result, dict):
            raise NativeOperationError("invalid_response")
        return result


STATUS_SCRIPT = r"""
$result = @{ defender = @{ available = $false; error = 'unavailable' }; firewall = @{ available = $false; error = 'unavailable' }; detections = @{ available = $false; error = 'unavailable'; items = @() } }
try {
  Import-Module (Join-Path $PSHOME 'Modules\Defender\Defender.psd1') -ErrorAction Stop
  $s = Defender\Get-MpComputerStatus -ErrorAction Stop
  $result.defender = @{ available = $true; mode = [string]$s.AMRunningMode;
    service_enabled = $s.AMServiceEnabled; antivirus_enabled = $s.AntivirusEnabled;
    realtime_enabled = $s.RealTimeProtectionEnabled; signature_version = [string]$s.AntivirusSignatureVersion;
    signature_updated_at = (Utc-Date $s.AntivirusSignatureLastUpdated);
    quick_scan_started_at = (Utc-Date $s.QuickScanStartTime); quick_scan_ended_at = (Utc-Date $s.QuickScanEndTime);
    full_scan_started_at = (Utc-Date $s.FullScanStartTime); full_scan_ended_at = (Utc-Date $s.FullScanEndTime) }
  try {
    $items = @(Defender\Get-MpThreatDetection -ErrorAction Stop | Select-Object -First 100 | ForEach-Object {
      @{ threat_id = [string]$_.ThreatID; detected_at = (Utc-Date $_.InitialDetectionTime);
         remediated_at = (Utc-Date $_.RemediationTime); last_changed_at = (Utc-Date $_.LastThreatStatusChangeTime);
         action_success = $_.ActionSuccess; status_id = $_.ThreatStatusID; cleaning_action_id = $_.CleaningActionID }
    })
    $result.detections = @{ available = $true; items = $items; limit = 100 }
  } catch { $result.detections.error = (Error-Code $_) }
} catch { $result.defender.error = (Error-Code $_) }
try {
  Import-Module (Join-Path $PSHOME 'Modules\NetSecurity\NetSecurity.psd1') -ErrorAction Stop
  $profiles = @(NetSecurity\Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop | ForEach-Object {
    @{ name = [string]$_.Name; enabled = [string]$_.Enabled; default_inbound = [string]$_.DefaultInboundAction; default_outbound = [string]$_.DefaultOutboundAction }
  })
  $result.firewall = @{ available = $true; profiles = $profiles }
} catch { $result.firewall.error = (Error-Code $_) }
$result | ConvertTo-Json -Compress -Depth 6
"""

SCAN_SCRIPT = r"""
try {
  $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
  Import-Module (Join-Path $PSHOME 'Modules\Defender\Defender.psd1') -ErrorAction Stop
  if ($request.kind -eq 'quick') { Defender\Start-MpScan -ScanType QuickScan -ErrorAction Stop }
  elseif ($request.kind -eq 'full') { Defender\Start-MpScan -ScanType FullScan -ErrorAction Stop }
  else { throw 'Invalid scan type' }
  @{ accepted = $true } | ConvertTo-Json -Compress
} catch { @{ accepted = $false; error = (Error-Code $_) } | ConvertTo-Json -Compress }
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _date(value: Any) -> datetime | None:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo and result.year >= 2000 else None
    except (AttributeError, ValueError, TypeError):
        return None


def _boolean(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


class SecurityProvider:
    """Status can be read without elevation where Windows permits it.

    start_scan is for the separate broker after explicit authorization. One
    in-memory request is tracked; Windows observations remain available after
    restart, but NetSentinel does not claim ownership of an untracked scan.
    """
    def __init__(self, runner: Any = None, clock: Callable[[], datetime] = utc_now):
        self.runner = runner or PowerShellRunner()
        self.clock = clock
        self._lock = threading.Lock()
        self._request: dict | None = None
        self._worker: threading.Thread | None = None

    def status(self) -> dict:
        observed = self.clock()
        try:
            raw = self.runner.run(STATUS_SCRIPT, timeout=20)
        except NativeOperationError as exc:
            raw = {key: {"available": False, "error": exc.code} for key in ("defender", "firewall", "detections")}
        result = {"source": "Windows Defender and NetSecurity", "provenance": "LIVE", "observed_at": observed.isoformat()}
        defender = raw.get("defender", {})
        if not isinstance(defender, dict):
            defender = {}
        if defender.get("available") is True:
            mode = str(defender.get("mode") or "Unknown")[:80]
            state = "active" if mode.lower() == "normal" else "passive" if "passive" in mode.lower() else "other"
            if defender.get("antivirus_enabled") is False or defender.get("service_enabled") is False:
                state = "disabled" if state != "passive" else state
            result["defender"] = {"available": True, "state": state, "mode": mode}
            for key in ("service_enabled", "antivirus_enabled", "realtime_enabled"):
                result["defender"][key] = _boolean(defender.get(key))
            for key in ("signature_updated_at", "quick_scan_started_at", "quick_scan_ended_at", "full_scan_started_at", "full_scan_ended_at"):
                parsed = _date(defender.get(key))
                result["defender"][key] = parsed.isoformat() if parsed else None
            updated = _date(defender.get("signature_updated_at"))
            result["defender"]["signature_age_seconds"] = (observed - updated).total_seconds() if updated and updated <= observed else None
            result["defender"]["signature_version"] = str(defender.get("signature_version") or "")[:80] or None
        else:
            result["defender"] = {"available": False, "state": "unavailable", "error": self._error(defender)}
        firewall = raw.get("firewall", {})
        if not isinstance(firewall, dict):
            firewall = {}
        profiles = {}
        for row in firewall.get("profiles", []) if isinstance(firewall.get("profiles"), list) else []:
            if isinstance(row, dict) and row.get("name") in ("Domain", "Private", "Public"):
                profiles[row["name"]] = {"name": row["name"], "available": True,
                    "enabled": {"True": True, "False": False}.get(str(row.get("enabled"))),
                    "default_inbound": str(row.get("default_inbound", "Unknown"))[:40],
                    "default_outbound": str(row.get("default_outbound", "Unknown"))[:40]}
        result["firewall"] = {"available": firewall.get("available") is True,
            "profiles": [profiles.get(name, {"name": name, "available": False, "enabled": None}) for name in ("Domain", "Private", "Public")]}
        if not result["firewall"]["available"]:
            result["firewall"]["error"] = self._error(firewall)
        detection = raw.get("detections", {})
        if not isinstance(detection, dict):
            detection = {}
        items = []
        for row in detection.get("items", [])[:100] if isinstance(detection.get("items"), list) else []:
            if not isinstance(row, dict):
                continue
            item = {"threat_id": str(row.get("threat_id", ""))[:40], "action_success": _boolean(row.get("action_success"))}
            for key in ("detected_at", "remediated_at", "last_changed_at"):
                parsed = _date(row.get(key))
                item[key] = parsed.isoformat() if parsed else None
            for key in ("status_id", "cleaning_action_id"):
                value = row.get(key)
                item[key] = value if type(value) is int and 0 <= value <= 2**32 - 1 else None
            items.append(item)
        result["detections"] = {"available": detection.get("available") is True, "items": items, "limit": 100,
            "scope": "Available Defender history; not attributed to a particular scan. Paths are omitted."}
        if not result["detections"]["available"]:
            result["detections"]["error"] = self._error(detection)
        result["limitations"] = ["Status is not a safety verdict.", "Unavailable fields are not disabled protection.",
            "Scan observations have no reliable percentage or NetSentinel scan ID."]
        return result

    @staticmethod
    def _error(value: dict) -> str:
        allowed = {"unsupported", "permission_denied", "timeout", "output_limit", "invalid_response", "native_failed", "unavailable"}
        return value.get("error") if value.get("error") in allowed else "unavailable"

    def start_scan(self, kind: str) -> dict:
        if kind not in ("quick", "full"):
            raise ValueError("Scan kind must be quick or full")
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                raise NativeOperationError("scan_busy")
            defender = self.status()["defender"]
            if not defender.get("available") or defender.get("state") != "active" or defender.get("antivirus_enabled") is not True:
                raise NativeOperationError("scan_unavailable")
            self._request = {"kind": kind, "requested_at": self.clock().isoformat(), "state": "requested", "error": None,
                             "previous_started_at": defender.get(kind + "_scan_started_at")}
            request = self._request

            def execute() -> None:
                try:
                    answer = self.runner.run(SCAN_SCRIPT, {"kind": kind}, timeout=86400)
                    with self._lock:
                        request["command_returned"] = True
                        if answer.get("accepted") is not True:
                            request.update(state="failed", error=self._error(answer))
                except NativeOperationError as exc:
                    with self._lock:
                        request.update(state="unknown" if exc.code == "timeout" else "failed", error=exc.code)

            self._worker = threading.Thread(target=execute, name="netsentinel-defender-scan", daemon=True)
            self._worker.start()
            return dict(request)

    def scan_status(self) -> dict:
        status = self.status()
        with self._lock:
            request = dict(self._request) if self._request else None
        defender = status["defender"]
        if request and request["state"] not in ("failed", "unknown"):
            kind = request["kind"]
            requested = _date(request["requested_at"])
            started = _date(defender.get(kind + "_scan_started_at"))
            ended = _date(defender.get(kind + "_scan_ended_at"))
            if not defender.get("available"):
                request["state"] = "unavailable"
            elif (requested and started and started >= requested - timedelta(seconds=1)
                  and started != _date(request.get("previous_started_at"))):
                request["state"] = "completed" if ended and ended >= started else "running"
            elif request.get("command_returned"):
                request["state"] = "completion_unconfirmed"
        return {"source": status["source"], "provenance": "LIVE", "observed_at": status["observed_at"],
            "request": request, "defender": defender, "detections": status["detections"],
            "limitations": ["No percentage is exposed by this interface.",
                "Timestamps may describe a scan started outside NetSentinel; completion does not mean the computer is safe.",
                "After restart, scan ownership is unknown; Windows observations remain available."]}
