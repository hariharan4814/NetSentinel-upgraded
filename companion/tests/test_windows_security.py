"""Offline SIMULATION fixtures; these tests never start Defender scans."""
import copy
import io
import json
from pathlib import Path
import subprocess
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from companion.windows_security import (
    NativeOperationError, PowerShellRunner, SCAN_SCRIPT, STATUS_SCRIPT, SecurityProvider,
)

NOW = datetime(2026, 10, 2, 12, 0, 0, 200000, tzinfo=timezone.utc)
BASE = {"defender": {"available": True, "mode": "Normal", "service_enabled": True,
    "antivirus_enabled": True, "realtime_enabled": True, "signature_version": "test-fixture",
    "signature_updated_at": "2026-10-02T11:00:00.200000Z",
    "quick_scan_started_at": "2026-10-01T11:00:00Z", "quick_scan_ended_at": "2026-10-01T11:03:00Z"},
    "firewall": {"available": True, "profiles": [{"name": "Domain", "enabled": "True"},
        {"name": "Private", "enabled": "False"}, {"name": "Public", "enabled": "NotConfigured"}]},
    "detections": {"available": True, "items": []}}


class FixtureRunner:
    def __init__(self):
        self.status = copy.deepcopy(BASE)
        self.result = {"accepted": True}
        self.calls = []
        self.release = threading.Event()
        self.release.set()

    def run(self, script, values=None, *, timeout=20):
        self.calls.append((script, values, timeout))
        if script == STATUS_SCRIPT:
            return copy.deepcopy(self.status)
        assert script == SCAN_SCRIPT
        self.release.wait(2)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class SecurityStatusTests(unittest.TestCase):
    def setUp(self):
        self.runner = FixtureRunner()
        self.provider = SecurityProvider(self.runner, clock=lambda: NOW)

    def test_actual_fields_nulls_and_three_profile_states(self):
        result = self.provider.status()
        self.assertEqual(result["defender"]["state"], "active")
        self.assertEqual(result["defender"]["signature_age_seconds"], 3600)
        self.assertIsNone(result["defender"]["full_scan_ended_at"])
        self.assertEqual([p["enabled"] for p in result["firewall"]["profiles"]], [True, False, None])
        self.assertNotIn("security_score", result)

    def test_passive_mode_not_misrepresented_as_active(self):
        self.runner.status["defender"].update(mode="Passive Mode", antivirus_enabled=False)
        result = self.provider.status()
        self.assertEqual(result["defender"]["state"], "passive")
        with self.assertRaisesRegex(NativeOperationError, "passive"):
            self.provider.start_scan("quick")
        self.assertFalse(any(call[0] == SCAN_SCRIPT for call in self.runner.calls))

    def test_disabled_and_unknown_modes_do_not_permit_scan(self):
        for fields, state in (({"antivirus_enabled": False}, "disabled"), ({"mode": "EDR Block Mode"}, "other")):
            self.runner.status["defender"] = {**BASE["defender"], **fields}
            self.assertEqual(self.provider.status()["defender"]["state"], state)
            with self.assertRaises(NativeOperationError):
                self.provider.start_scan("full")

    def test_unavailable_defender_does_not_hide_firewall(self):
        self.runner.status["defender"] = {"available": False, "error": "permission_denied"}
        result = self.provider.status()
        self.assertFalse(result["defender"]["available"])
        self.assertTrue(result["firewall"]["available"])
        self.assertEqual(result["defender"]["error"], "permission_denied")

    def test_runner_unavailable_is_not_disabled_or_zero(self):
        self.runner.run = Mock(side_effect=NativeOperationError("unsupported"))
        result = self.provider.status()
        self.assertFalse(result["defender"]["available"])
        self.assertFalse(result["detections"]["available"])
        self.assertTrue(all(row["enabled"] is None for row in result["firewall"]["profiles"]))

    def test_future_and_invalid_dates_have_unavailable_age(self):
        for timestamp in ("2028-01-01T00:00:00Z", "invalid", "2026-01-01T00:00:00", None):
            self.runner.status["defender"]["signature_updated_at"] = timestamp
            self.assertIsNone(self.provider.status()["defender"]["signature_age_seconds"])

    def test_detection_redaction_and_retention_bound(self):
        self.runner.status["detections"]["items"] = [{"threat_id": "1234", "action_success": False,
            "status_id": 2, "resources": ["private-path"], "password": "secret", "detected_at": "2026-10-02T10:00:00Z"}] * 150
        result = self.provider.status()["detections"]
        self.assertEqual(len(result["items"]), 100)
        self.assertNotIn("private-path", json.dumps(result))
        self.assertNotIn("secret", json.dumps(result))
        self.assertFalse(result["items"][0]["action_success"])

    def test_scan_validates_kind_before_native_call(self):
        for kind in ("CustomScan", "QuickScan; malicious", "quick\n", None):
            with self.assertRaises(ValueError):
                self.provider.start_scan(kind)
        self.assertEqual(self.runner.calls, [])

    def test_second_scan_is_refused_while_request_runs(self):
        self.runner.release.clear()
        first = self.provider.start_scan("quick")
        self.assertEqual(first["state"], "requested")
        with self.assertRaises(NativeOperationError) as caught:
            self.provider.start_scan("full")
        self.assertEqual(caught.exception.code, "scan_busy")
        self.runner.release.set()
        self.provider._worker.join(2)

    def test_cmdlet_success_is_not_completion_without_new_observation(self):
        self.provider.start_scan("quick")
        self.provider._worker.join(2)
        result = self.provider.scan_status()
        self.assertEqual(result["request"]["state"], "completion_unconfirmed")
        self.assertNotIn("progress", result)

    def test_new_windows_timestamps_show_running_then_completed(self):
        self.provider.start_scan("quick")
        self.provider._worker.join(2)
        self.runner.status["defender"]["quick_scan_started_at"] = "2026-10-02T12:00:00Z"
        self.assertEqual(self.provider.scan_status()["request"]["state"], "running")
        self.runner.status["defender"]["quick_scan_ended_at"] = "2026-10-02T12:03:00Z"
        self.assertEqual(self.provider.scan_status()["request"]["state"], "completed")

    def test_native_rejection_and_timeout_remain_explicit(self):
        for result, expected in (({"accepted": False, "error": "permission_denied"}, "failed"),
                                 (NativeOperationError("timeout"), "unknown")):
            self.runner.result = result
            self.provider.start_scan("full")
            self.provider._worker.join(2)
            self.assertEqual(self.provider.scan_status()["request"]["state"], expected)

    def test_after_restart_no_invented_scan_ownership(self):
        self.assertIsNone(self.provider.scan_status()["request"])
        self.assertEqual(self.provider.scan_status()["defender"]["quick_scan_ended_at"], "2026-10-01T11:03:00+00:00")


class FakeProcess:
    def __init__(self, output=b'{"ok": true}', stderr=b'', *, timeout=False):
        self.stdin = Mock()
        self.stdout = io.BytesIO(output)
        self.stderr = io.BytesIO(stderr)
        self.returncode = 0
        self.timeout = timeout
        self.killed = False

    def wait(self, timeout=None):
        if self.timeout and not self.killed:
            raise subprocess.TimeoutExpired("fixed command", timeout)
        return self.returncode

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed = True


class NativeRunnerTests(unittest.TestCase):
    def run_fixture(self, process, values=None):
        with patch("companion.windows_security.system_directory", return_value=Path("C:/Windows/System32")), \
             patch.object(Path, "is_file", return_value=True), \
             patch("companion.windows_security.subprocess.Popen", return_value=process) as popen:
            result = PowerShellRunner().run("fixed trusted script", values)
        return result, popen.call_args

    def test_values_are_stdin_data_not_command_interpolation(self):
        malicious = "'; Write-Output private; '"
        process = FakeProcess()
        result, arguments = self.run_fixture(process, {"path": malicious})
        self.assertEqual(result, {"ok": True})
        self.assertNotIn(malicious, str(arguments.args))
        self.assertFalse(arguments.kwargs["shell"])
        self.assertEqual(json.loads(process.stdin.write.call_args.args[0]), {"path": malicious})

    def test_oversized_response_terminates_before_returning_data(self):
        process = FakeProcess(b"x" * (PowerShellRunner.MAX_OUTPUT + 1))
        with self.assertRaises(NativeOperationError) as caught:
            self.run_fixture(process)
        self.assertEqual(caught.exception.code, "output_limit")
        self.assertTrue(process.killed)

    def test_timeout_kills_helper_and_does_not_leak_stderr(self):
        process = FakeProcess(stderr=b"private-user-folder", timeout=True)
        with self.assertRaises(NativeOperationError) as caught:
            self.run_fixture(process)
        self.assertEqual(caught.exception.code, "timeout")
        self.assertNotIn("private", str(caught.exception))
        self.assertTrue(process.killed)

    def test_invalid_json_is_a_sanitized_error(self):
        with self.assertRaises(NativeOperationError) as caught:
            self.run_fixture(FakeProcess(b"sensitive native failure"))
        self.assertEqual(caught.exception.code, "invalid_response")
        self.assertNotIn("sensitive", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
