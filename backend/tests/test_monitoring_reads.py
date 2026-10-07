from datetime import timedelta
from uuid import uuid4
from django.utils import timezone
from rest_framework.test import APITestCase
from monitoring.models import CaptureStatus, MonitoringSession
from .support import ScopedFixtureClient


class MonitoringReadTests(APITestCase):
    client_class = ScopedFixtureClient
    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"
        self.now = timezone.now()
        self.session = MonitoringSession.objects.create(
            source_id=uuid4(), run_id=uuid4(), interface_name="fixture-interface",
            mode="SIMULATION", started_at=self.now - timedelta(days=2),
            observation_profile="read-fixture", payload_digest="fixture")

    def get(self, route, **changes):
        return self.client.get(f"/api/v1/{route}/", {
            "session_id": str(self.session.pk), "mode": "SIMULATION", **changes})

    def status(self, seconds=0, session=None):
        return CaptureStatus.objects.create(
            session=session or self.session, observed_at=self.now - timedelta(seconds=seconds),
            state="RECOVERING", valid=False, reason="fixture_gap",
            loss_started_at=self.now - timedelta(seconds=seconds + 5),
            monitoring_gap_seconds=5, recovery_attempts=2, payload_digest="fixture")

    def test_both_reads_require_valid_session_and_mode(self):
        for route in ("capture-status", "monitoring-sessions"):
            for query in ({}, {"session_id": str(self.session.pk)}, {"mode": "SIMULATION"},
                          {"session_id": "invalid", "mode": "SIMULATION"},
                          {"session_id": str(self.session.pk), "mode": "OTHER"}):
                with self.subTest(route=route, query=query):
                    self.assertEqual(self.client.get(f"/api/v1/{route}/", query).status_code, 400)

    def test_status_read_isolates_session_and_mode(self):
        wanted = self.status()
        other = MonitoringSession.objects.create(
            source_id=uuid4(), run_id=uuid4(), interface_name="other", mode="LIVE",
            started_at=self.now - timedelta(days=2), observation_profile="fixture", payload_digest="fixture")
        self.status(session=other)
        self.assertEqual([r["id"] for r in self.get("capture-status").data["results"]], [str(wanted.pk)])
        self.assertEqual(self.get("capture-status", mode="LIVE").data["results"], [])
        self.assertEqual(self.get("capture-status", session_id=str(other.pk)).data["results"], [])
        self.assertEqual(self.get("capture-status", session_id=str(uuid4())).data["results"], [])

    def test_status_order_limit_and_cursor(self):
        rows = [self.status(seconds=i) for i in range(55)]
        self.assertEqual(len(self.get("capture-status").data["results"]), 50)
        response = self.get("capture-status", limit=2)
        self.assertEqual([r["id"] for r in response.data["results"]], [str(r.pk) for r in rows[:2]])
        from urllib.parse import urlsplit
        next_url = urlsplit(response.data["next"])
        second = self.client.get(next_url.path + "?" + next_url.query)
        self.assertEqual([r["id"] for r in second.data["results"]], [str(r.pk) for r in rows[2:4]])
        for limit in (0, -1, 201, "bad"):
            self.assertEqual(self.get("capture-status", limit=limit).status_code, 400)
        self.assertEqual(self.get("capture-status", limit=200).status_code, 200)

    def test_status_uses_observation_time_not_receipt_time(self):
        self.status(seconds=86401)
        self.status(seconds=-60)
        self.assertEqual(self.get("capture-status").data["results"], [])

    def test_status_exposes_exact_provenance_and_stored_gap_fields(self):
        self.status()
        response = self.get("capture-status")
        row = response.data["results"][0]
        self.assertEqual(set(row), {"id", "session_id", "received_at", "observed_at", "state",
                         "valid", "reason", "loss_started_at", "gap_ended_at", "monitoring_gap_seconds",
                         "recovery_attempts", "run_id", "mode", "interface_name"})
        self.assertEqual(row["run_id"], str(self.session.run_id))
        self.assertEqual(row["interface_name"], self.session.interface_name)
        self.assertEqual(row["mode"], "SIMULATION")
        self.assertEqual(row["monitoring_gap_seconds"], 5)
        self.assertEqual(row["recovery_attempts"], 2)
        self.assertIsNone(row["gap_ended_at"])
        self.assertFalse(row["valid"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_session_read_exact_metadata_even_when_session_is_old(self):
        response = self.get("monitoring-sessions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"session_id", "source_id", "run_id", "interface_name", "mode",
                         "started_at", "observation_profile", "schema_version", "received_at"})
        for key in ("session_id", "source_id", "run_id", "interface_name", "mode", "observation_profile", "schema_version"):
            self.assertEqual(response.data[key], str(getattr(self.session, key)))
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_session_unknown_or_wrong_mode_returns_same_not_found(self):
        unknown = self.get("monitoring-sessions", session_id=str(uuid4()))
        mismatch = self.get("monitoring-sessions", mode="LIVE")
        self.assertEqual((unknown.status_code, mismatch.status_code), (404, 404))
        self.assertEqual(unknown.data, mismatch.data)
