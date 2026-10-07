"""Deterministic control state tests; no Windows rule or scan is performed."""
import unittest
from unittest.mock import Mock, patch
from companion.broker import Broker
from companion.http_boundary import APIError
from companion.service import Companion
from companion.store import Store

NOW = 1790938800.0


class FixtureBroker:
    def __init__(self):
        self.owned = set()
        self.calls = []
        self.available = True
        self.fail_block = False
        self.fail_cleanup = False

    def call(self, action, data=None):
        self.calls.append((action, data))
        if not self.available:
            raise APIError(503, "fixture unavailable")
        if action == "rules":
            return {"success": True, "rules": [dict(app_id=app, direction=direction, enabled=True, action="Block")
                    for app in self.owned for direction in ("Inbound", "Outbound")]}
        if action == "block":
            if self.fail_block:
                return {"success": False, "state": "failed", "traffic_blocking_verified": False}
            self.owned.add(data["app"])
        if action == "unblock":
            self.owned.discard(data["app"])
        if action == "cleanup":
            if self.fail_cleanup:
                return {"success": False}
            self.owned.clear()
        return {"success": True, "traffic_blocking_verified": False}


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:", lambda: NOW)
        self.app_id = self.store.discover(r"C:\FixtureApplications\browser.exe")
        self.broker = FixtureBroker()
        self.collector = Mock()
        self.collector.view.return_value = {"state": "stopped"}
        self.app = Companion(self.store, self.broker, self.collector, Mock())

    def tearDown(self):
        self.store.close()

    def block(self):
        self.app.action("enforcement", {"enabled": True, "consent": True})
        self.app.action("control", {"app": self.app_id, "action": "block"})

    def test_manual_block_requires_enforcement_and_consent(self):
        with self.assertRaises(APIError):
            self.app.action("control", {"app": self.app_id, "action": "block"})
        with self.assertRaises(ValueError):
            self.app.action("enforcement", {"enabled": True, "consent": False})
        self.assertFalse(self.broker.owned)
        self.block()
        self.assertEqual(self.broker.owned, {self.app_id})
        self.assertFalse(self.app.controls[self.app_id]["traffic_blocking_verified"])

    def test_failures_do_not_claim_rules_applied_and_retries_are_bounded(self):
        self.broker.fail_block = True
        self.block()
        self.assertFalse(self.app.applied)
        before = len([action for action, _ in self.broker.calls if action == "block"])
        self.app.reconcile()
        self.assertEqual(len([action for action, _ in self.broker.calls if action == "block"]), before)
        self.assertFalse(self.app.controls[self.app_id]["success"])

    def test_disable_persists_observation_only_even_if_cleanup_fails(self):
        self.block()
        self.broker.fail_cleanup = True
        with self.assertRaises(APIError):
            self.app.action("enforcement", {"enabled": False, "consent": True})
        self.assertFalse(self.store.setting("enforcement"))
        self.assertTrue(any(event["code"] == "cleanup_unconfirmed" for event in self.store.snapshot()["events"]))

    def test_unblock_after_temporary_broker_disconnect_removes_existing_rule(self):
        self.block()
        self.broker.available = False
        self.app.reconcile()
        self.app.action("control", {"app": self.app_id, "action": "unblock"})
        self.broker.available = True
        self.app.reconcile()
        self.assertNotIn(self.app_id, self.broker.owned)

    def test_broker_restart_cleanup_is_detected_and_desired_rules_reapplied(self):
        self.block()
        self.broker.owned.clear()  # Broker restart/lease expiry cleaned only owned rules.
        self.app.reconcile()
        self.assertIn(self.app_id, self.broker.owned)

    def test_shutdown_attempts_cleanup_and_records_unconfirmed_failure(self):
        self.block()
        self.app.stop()
        self.assertFalse(self.broker.owned)
        self.collector.stop.assert_called_once()
        self.broker.available = False
        self.app.stop()
        self.assertTrue(any(event["code"] == "shutdown_cleanup_unconfirmed" for event in self.store.snapshot()["events"]))

    def test_control_api_rejects_arbitrary_path_command_and_scan_without_consent(self):
        for action, data in (("control", {"app": self.app_id, "action": "block", "path": r"C:\arbitrary.exe"}),
                             ("powershell", {"command": "whoami"}),
                             ("policy", {"app": self.app_id, "changes": {"unknown": 1}}),
                             ("scan", {"kind": "full", "consent": False})):
            with self.assertRaises((ValueError, APIError)):
                self.app.action(action, data)
        self.assertFalse(any(action == "scan" for action, _ in self.broker.calls))

    def test_broker_requires_independent_observed_executable_and_fixed_actions(self):
        firewall, security = Mock(), Mock()
        broker = Broker(firewall, security)
        with self.assertRaises(APIError):
            broker.action("block", {"app": self.app_id, "executable": r"C:\arbitrary.exe"})
        with self.assertRaises(ValueError):
            broker.resolve(r"C:\arbitrary.exe")
        with patch.object(broker, "resolve", return_value=r"c:\fixtureapplications\browser.exe") as resolve:
            broker.action("block", {"app": self.app_id})
            resolve.assert_called_once_with(self.app_id)
        with self.assertRaises(APIError):
            broker.action("scan", {"kind": "full", "consent": False})
        security.start_scan.assert_not_called()


if __name__ == "__main__":
    unittest.main()
