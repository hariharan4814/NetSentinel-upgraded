import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from companion.attribution import Snapshot, SocketOwner, match_packet
from companion.identity import canonical, executable_id, protected
from companion.store import Store, reset_times
from sensor.models import PacketMetadata

APP = r"C:\TestApps\browser.exe"
OTHER = r"C:\TestApps\other.exe"
NOW = datetime(2026, 10, 2, 12, tzinfo=timezone.utc).timestamp()


def packet(size=600, at=NOW, direction="outbound", incomplete=False):
    return PacketMetadata(at, "test-fixture", "192.0.2.1", "198.51.100.1", 1200, 443,
                          "TCP", size, direction, incomplete, False)


class AttributionTests(unittest.TestCase):
    def owner(self, path=APP, pid=1):
        return SocketOwner("TCP", "192.0.2.1", 1200, "198.51.100.1", 443, canonical(path) if path else None, pid)

    def test_same_executable_subprocess_grouping(self):
        snapshot = Snapshot(NOW, (self.owner(), self.owner(pid=2)))
        self.assertEqual(match_packet(packet(), snapshot, NOW), canonical(APP))
        self.assertEqual(executable_id(APP.upper()), executable_id(APP))

    def test_ambiguous_unknown_stale_fragment_unassigned(self):
        for owners in [(self.owner(), self.owner(OTHER)), (self.owner(), self.owner(None))]:
            self.assertIsNone(match_packet(packet(), Snapshot(NOW, owners), NOW))
        self.assertIsNone(match_packet(packet(), Snapshot(NOW-3, (self.owner(),)), NOW))
        self.assertIsNone(match_packet(packet(incomplete=True), Snapshot(NOW, (self.owner(),)), NOW))
        self.assertIsNone(match_packet(packet(), Snapshot(NOW, (self.owner(),), False), NOW))

    def test_udp_wildcard_ambiguity_and_tcp_listener(self):
        udp = PacketMetadata(NOW, "fixture", "192.0.2.1", "198.51.100.1", 1200, 53, "UDP", 100, "outbound")
        owner = SocketOwner("UDP", "0.0.0.0", 1200, None, None, canonical(APP))
        self.assertEqual(match_packet(udp, Snapshot(NOW, (owner,)), NOW), canonical(APP))
        other = SocketOwner("UDP", "0.0.0.0", 1200, None, None, None)
        self.assertIsNone(match_packet(udp, Snapshot(NOW, (owner, other)), NOW))
        listener = SocketOwner("TCP", "0.0.0.0", 1200, None, None, canonical(APP))
        self.assertIsNone(match_packet(packet(), Snapshot(NOW, (listener,)), NOW))

    def test_path_validation_and_critical_protection(self):
        for bad in [r"\\server\share\app.exe", r"C:\app.exe:stream", "app.exe", r"C:app.exe", r"C:\*.exe"]:
            with self.assertRaises(ValueError):
                canonical(bad)
        self.assertTrue(protected(r"C:\Windows\System32\svchost.exe"))


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = NOW
        self.path = Path(self.tmp.name)/"state.sqlite3"
        self.store = Store(self.path, lambda: self.now)
        self.app = self.store.discover(APP)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def item(self, mode="LIVE"):
        return self.store.snapshot(mode)["apps"][0]

    def test_thresholds_restart_and_modes(self):
        self.store.policy(self.app, {"daily": 2000, "warning": 50, "auto": True})
        self.store.record([(self.app, packet(1000))])
        self.assertFalse(self.item()["should_block"])
        self.assertTrue(any(e["code"] == "quota_warning" for e in self.store.snapshot()["events"]))
        self.store.record([(self.app, packet(1000))])
        self.assertTrue(self.item()["should_block"])
        self.assertEqual(self.item("SIMULATION")["today"]["combined"], 0)
        self.store.close()
        self.store = Store(self.path, lambda: self.now)
        self.assertTrue(self.item()["should_block"])
        self.assertEqual(self.item()["today"]["combined"], 2000)

    def test_override_expires_at_utc_reset(self):
        self.store.policy(self.app, {"monthly": 1024, "auto": True})
        self.store.record([(self.app, packet(2048))])
        self.store.control(self.app, "override")
        self.assertFalse(self.item()["should_block"])
        self.now = datetime(2026, 11, 1, tzinfo=timezone.utc).timestamp()
        self.assertEqual(self.item()["month"]["combined"], 0)
        self.store.record([(self.app, packet(2048, self.now))])
        self.assertTrue(self.item()["should_block"])

    def test_daily_reset_manual_and_directions(self):
        self.store.policy(self.app, {"daily": 1024, "direction": "download", "auto": True})
        self.store.record([(self.app, packet(2048))])
        self.assertFalse(self.item()["should_block"])
        self.store.control(self.app, "block")
        self.assertTrue(self.item()["should_block"])
        self.store.control(self.app, "unblock")
        self.assertFalse(self.item()["should_block"])
        self.now += 86400
        self.assertEqual(self.item()["today"]["combined"], 0)

    def test_unassigned_flow_and_provenance(self):
        self.store.record([(None, packet(123)), (self.app, packet(321))], "SIMULATION")
        sim = self.store.snapshot("SIMULATION")
        self.assertEqual(sim["unassigned_today"], 123)
        self.assertEqual(sum(f["up"] for f in sim["flows"]), 444)
        self.assertEqual(self.store.snapshot()["flows"], [])
        with self.assertRaises(ValueError):
            self.store.record([], "DEMO")

    def test_validation_and_protection(self):
        for value in [-1, 1.5, True, 10**16]:
            with self.assertRaises(ValueError):
                self.store.policy(self.app, {"daily": value})
        with self.assertRaises(ValueError):
            self.store.policy(self.app, {"path": OTHER})
        critical = self.store.discover(r"C:\Windows\System32\svchost.exe")
        with self.assertRaises(ValueError):
            self.store.policy(critical, {"auto": True})
        with self.assertRaises(ValueError):
            self.store.control(critical, "block")

    def test_events_and_time_retention_are_bounded(self):
        for i in range(2010):
            self.store.event("control", "fixture", str(i), mode="SIMULATION")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM events").fetchone()[0], 2000)
        self.now += 91*86400
        self.assertEqual(self.store.snapshot("SIMULATION")["events"], [])

    def test_december_month_boundary(self):
        now = datetime(2026, 12, 31, 23, tzinfo=timezone.utc).timestamp()
        daily, monthly = reset_times(now)
        self.assertEqual(daily, monthly)
        self.assertEqual(datetime.fromtimestamp(monthly, timezone.utc).year, 2027)


if __name__ == "__main__":
    unittest.main()
