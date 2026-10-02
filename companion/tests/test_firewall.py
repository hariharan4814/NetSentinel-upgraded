"""SIMULATION rule fixtures. Never import native NetSecurity or change host rules."""
import hashlib
import ntpath
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from companion.firewall import FIREWALL_SCRIPT, FirewallController, canonical_executable
from companion.windows_security import NativeOperationError, PowerShellRunner

EXECUTABLE = r"c:\apps\controlled-test.exe"
IDENTITY = hashlib.sha256(EXECUTABLE.encode()).hexdigest()
RULE = "NetSentinel.Companion.v1." + IDENTITY


class FirewallTests(unittest.TestCase):
    def setUp(self):
        self.runner = Mock()
        self.runner.run.return_value = {"success": True, "state": "applied_not_traffic_verified", "rule_names": [RULE + ".in", RULE + ".out"]}
        self.controller = FirewallController(self.runner)

    def test_block_checks_identity_and_keeps_program_in_data(self):
        with patch("companion.firewall.canonical_executable", return_value=EXECUTABLE):
            result = self.controller.block(EXECUTABLE, IDENTITY)
        self.assertTrue(result["success"])
        self.assertFalse(result["traffic_blocking_verified"])
        args = self.runner.run.call_args
        self.assertIs(args.args[0], FIREWALL_SCRIPT)
        self.assertEqual(args.args[1], {"operation": "block", "executable": EXECUTABLE, "app_id": IDENTITY})
        self.assertNotIn(EXECUTABLE, args.args[0])

    def test_mismatched_identity_and_invalid_id_fail_before_native_call(self):
        with patch("companion.firewall.canonical_executable", return_value=EXECUTABLE):
            with self.assertRaises(ValueError):
                self.controller.block(EXECUTABLE, "0" * 64)
        for identity in ("*", "" , IDENTITY.upper(), IDENTITY + ".in", None):
            with self.assertRaises(ValueError):
                self.controller.unblock(identity)
        self.runner.run.assert_not_called()

    def test_noncanonical_and_special_paths_are_rejected(self):
        for executable in (r"\\server\share\app.exe", r"\\?\C:\app.exe", "app.exe", r"c:app.exe",
                           r"C:\app.exe:stream", r"C:\folder\..\app.exe", r"C:\*.exe", "C:\\app.exe\n",
                           r"C:\folder.\app.exe", r"C:\app.dll"):
            with self.subTest(executable=executable), self.assertRaises(ValueError):
                canonical_executable(executable)

    @unittest.skipUnless(os.name == "nt", "Existing Windows executable canonicalization")
    def test_existing_canonical_file_required(self):
        import sys
        expected = ntpath.normcase(ntpath.normpath(str(Path(sys.executable).resolve())))
        self.assertEqual(canonical_executable(str(Path(sys.executable).resolve())), expected)
        with self.assertRaises(ValueError):
            canonical_executable(r"C:\not-existing-netsentinel-test\app.exe")

    def test_failure_and_partial_rollback_are_not_success(self):
        self.runner.run.return_value = {"success": False, "state": "failed", "error": "permission_denied", "rollback_failed": [RULE + ".in"]}
        with patch("companion.firewall.canonical_executable", return_value=EXECUTABLE):
            result = self.controller.block(EXECUTABLE, IDENTITY)
        self.assertFalse(result["success"])
        self.assertEqual(result["rollback_failed"], [RULE + ".in"])

    def test_cleanup_is_exact_fixed_operation_and_retains_failure(self):
        self.runner.run.return_value = {"success": False, "state": "removed", "ownership_conflicts": 2}
        result = self.controller.cleanup()
        self.assertEqual(self.runner.run.call_args.args[1], {"operation": "cleanup"})
        self.assertFalse(result["success"])
        self.assertEqual(result["ownership_conflicts"], 2)
        self.assertNotIn("Reset-NetFirewall", FIREWALL_SCRIPT)
        self.assertNotIn("netsh", FIREWALL_SCRIPT)

    def test_remove_can_report_partial_failure(self):
        self.runner.run.return_value = {"success": False, "state": "failed", "error": "permission_denied", "removed": [RULE + ".in"]}
        result = self.controller.unblock(IDENTITY)
        self.assertFalse(result["success"])
        self.assertEqual(result["removed"], [RULE + ".in"])

    def test_private_unexpected_native_data_is_not_returned(self):
        self.runner.run.return_value = {"success": True, "state": "observed_rules", "executable": "sensitive-path", "rules": [
            {"app_id": IDENTITY, "direction": "Outbound", "enabled": "True", "action": "Block", "program": "private"}],
            "rule_names": ["unrelated-user-rule", RULE + ".in"]}
        result = self.controller.rules()
        self.assertEqual(result["rule_names"], [RULE + ".in"])
        self.assertNotIn("private", str(result))
        self.assertNotIn("sensitive", str(result))

    def test_native_timeout_and_unexpected_response_remain_explicit(self):
        self.runner.run.side_effect = NativeOperationError("timeout")
        with self.assertRaises(NativeOperationError):
            self.controller.cleanup()
        self.runner.run.side_effect = None
        self.runner.run.return_value = {"success": "true"}
        with self.assertRaises(NativeOperationError):
            self.controller.rules()


# The production script is exercised against a memory-only module bearing the
# qualified NetSecurity name. No real NetSecurity module is imported. Opt in to
# these integration fixtures on Windows; they cannot create host firewall rules.
MOCK_MODULE = r"""
$null = New-Module -Name NetSecurity -ScriptBlock {
  $script:rules = @{}
  function Get-NetFirewallRule {
    param($PolicyStore, $Name, $ErrorAction)
    if ($Name) { if ($script:rules.ContainsKey($Name)) { return $script:rules[$Name] }; return }
    return @($script:rules.Values)
  }
  function New-NetFirewallRule {
    param($PolicyStore, $Name, $DisplayName, $Description, $Group, $Direction, $Action, $Enabled, $Profile, $Program, $Protocol, $ErrorAction)
    if ($global:fixtureFailure -and $Direction -eq 'Outbound') { throw 'fixture create failure' }
    $script:rules[$Name] = [pscustomobject]@{ Name=$Name; Description=$Description; Group=$Group; Direction=$Direction; Action=$Action; Enabled=$Enabled; Profile=$Profile; Program=$Program }
    return $script:rules[$Name]
  }
  function Remove-NetFirewallRule {
    param([Parameter(ValueFromPipeline=$true)]$InputObject)
    process { if ($global:fixtureRollbackFailure) { throw 'fixture removal failure' }; $script:rules.Remove($InputObject.Name) }
  }
  function Get-NetFirewallApplicationFilter {
    param([Parameter(ValueFromPipeline=$true)]$InputObject)
    process { return [pscustomobject]@{ Program=$InputObject.Program } }
  }
  function Add-FixtureRule {
    param($Name, $Group, $Description)
    $script:rules[$Name] = [pscustomobject]@{ Name=$Name; Description=$Description; Group=$Group; Direction='Inbound'; Action='Block'; Enabled='True'; Profile='Any'; Program='c:\apps\controlled-test.exe' }
  }
  Export-ModuleMember -Function *
} | Import-Module -PassThru
function Test-Path { param($LiteralPath, $PathType) return $true }
"""


@unittest.skipUnless(os.name == "nt" and os.environ.get("NETSENTINEL_POWERSHELL_FIXTURE") == "1",
                     "Set NETSENTINEL_POWERSHELL_FIXTURE=1 for memory-only PowerShell script fixtures")
class PowerShellFirewallFixtures(unittest.TestCase):
    def run_fixture(self, operation, setup=""):
        script = FIREWALL_SCRIPT.replace("Import-Module (Join-Path $PSHOME 'Modules\\NetSecurity\\NetSecurity.psd1') -ErrorAction Stop", "# Native module intentionally absent from this SIMULATION fixture")
        return PowerShellRunner().run(MOCK_MODULE + setup + script,
            {"operation": operation, "app_id": IDENTITY, "executable": EXECUTABLE}, timeout=20)

    def test_actual_script_applies_both_mock_directions(self):
        result = self.run_fixture("block")
        self.assertTrue(result["success"], result)
        self.assertEqual(result["rule_names"], [RULE + ".in", RULE + ".out"])

    def test_actual_script_rolls_back_first_rule_when_second_fails(self):
        result = self.run_fixture("block", "$global:fixtureFailure = $true\n")
        self.assertFalse(result["success"])
        self.assertEqual(result["rollback_failed"], [])

    def test_actual_script_reports_failed_rollback(self):
        result = self.run_fixture("block", "$global:fixtureFailure = $true\n$global:fixtureRollbackFailure = $true\n")
        self.assertFalse(result["success"])
        self.assertEqual(result["rollback_failed"], [RULE + ".in"])

    def test_actual_cleanup_skips_conflicting_rule(self):
        setup = "Add-FixtureRule -Name '" + RULE + ".in' -Group 'NetSentinel.Companion.v1' -Description 'another owner'\n"
        result = self.run_fixture("cleanup", setup)
        self.assertFalse(result["success"])
        self.assertEqual(result["ownership_conflicts"], 1)
        self.assertEqual(result["removed"], [])

    def test_actual_cleanup_removes_only_matching_owned_rule(self):
        setup = "Add-FixtureRule -Name '" + RULE + ".in' -Group 'NetSentinel.Companion.v1' -Description 'NetSentinel owned application block v1'\n"
        setup += "Add-FixtureRule -Name 'unrelated-rule' -Group 'Another group' -Description 'user rule'\n"
        result = self.run_fixture("cleanup", setup)
        self.assertTrue(result["success"])
        self.assertEqual(result["removed"], [RULE + ".in"])


if __name__ == "__main__":
    unittest.main()
