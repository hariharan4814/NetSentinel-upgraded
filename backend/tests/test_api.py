"""Synthetic metadata only. This suite opens no capture device or external socket."""
from copy import deepcopy
from datetime import timedelta, timezone as dt_timezone
from io import StringIO
from uuid import uuid4
from unittest.mock import patch

from django.core.management import call_command
from django.db import IntegrityError, OperationalError, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from monitoring.models import MonitoringSession, CaptureStatus
from telemetry.models import TelemetrySample, TrafficWindow
from telemetry.serializers import TelemetrySampleSerializer
from .support import ScopedFixtureClient


class BackendTests(APITestCase):
    client_class = ScopedFixtureClient
    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"
        now = timezone.now() - timedelta(minutes=2)
        self.start = now.replace(second=now.second // 10 * 10, microsecond=0)
        self.session = {
            "session_id": str(uuid4()), "source_id": str(uuid4()), "run_id": str(uuid4()),
            "interface_name": "fixture-interface", "mode": "LIVE",
            "started_at": self.start.isoformat(), "observation_profile": "host-v1-fixture",
        }
        self.assertEqual(self.post("monitoring-sessions", self.session).status_code, 201)

    def post(self, endpoint, data):
        return self.client.post(f"/api/v1/{endpoint}/", data, format="json")

    def identity(self):
        return {"id": str(uuid4()), **{key: self.session[key] for key in (
            "session_id", "run_id", "mode", "interface_name")}}

    def sample(self):
        return {**self.identity(), "observed_at": (self.start + timedelta(seconds=1)).isoformat(),
                "elapsed_seconds": 1, "valid": True, "reason": None,
                "bytes_sent": 100, "bytes_received": 200, "packets_sent": 2, "packets_received": 3,
                "delta_bytes_sent": 50, "delta_bytes_received": 100,
                "delta_packets_sent": 1, "delta_packets_received": 2,
                "upload_bytes_per_second": 50, "download_bytes_per_second": 100}

    def window(self):
        return {**self.identity(), "start": (self.start + timedelta(seconds=10)).isoformat(),
                "end": (self.start + timedelta(seconds=20)).isoformat(),
                "finalized_at": (self.start + timedelta(seconds=22)).isoformat(),
                "processed_at": (self.start + timedelta(seconds=22.1)).isoformat(),
                "partial": False, "valid": True, "reason": None,
                "packets": 3, "ip_bytes": 180, "outbound_packets": 2, "inbound_packets": 1,
                "outbound_bytes": 120, "inbound_bytes": 60, "tcp_packets": 2, "udp_packets": 1,
                "flow_count": 2}

    def status(self):
        return {**self.identity(), "observed_at": (self.start + timedelta(seconds=2)).isoformat(),
                "state": "INTERFACE_LOST", "valid": False, "reason": "interface_unavailable",
                "loss_started_at": (self.start + timedelta(seconds=2)).isoformat()}

    def recent(self, endpoint, **kwargs):
        return self.client.get(f"/api/v1/{endpoint}/", {
            "session_id": self.session["session_id"], "mode": "LIVE", **kwargs})

    def test_health_checks_database(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database"], "reachable")
        with patch("monitoring.views.connection.cursor", side_effect=OperationalError("private database detail")):
            response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", str(response.data))

    def test_database_failure_is_explicit_and_redacted_on_ingestion(self):
        with patch("django.db.models.query.QuerySet.get", side_effect=OperationalError("password details")):
            response = self.post("telemetry", self.sample())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("password", str(response.data))

    def test_only_six_application_models(self):
        from django.apps import apps
        self.assertEqual({model.__name__ for model in apps.get_models()},
                           {"MonitoringSession", "CaptureStatus", "TelemetrySample", "TrafficWindow", "ModelVersion", "AnomalyResult"})

    def test_round_trip_records_preserves_session_provenance_and_utc(self):
        for endpoint, data in [("telemetry", self.sample()), ("windows", self.window()), ("capture-status", self.status())]:
            with self.subTest(endpoint=endpoint):
                response = self.post(endpoint, data)
                self.assertEqual(response.status_code, 201, response.data)
                for name in ("session_id", "run_id", "mode", "interface_name", "valid", "reason"):
                    self.assertEqual(response.data[name], data[name])
                self.assertIn("received_at", response.data)
                self.assertNotIn("payload_digest", response.data)
        self.assertEqual(len(self.recent("telemetry").data["results"]), 1)
        self.assertEqual(len(self.recent("windows").data["results"]), 1)

    def test_session_retry_and_immutable_identity(self):
        self.assertEqual(self.post("monitoring-sessions", self.session).status_code, 200)
        for field, changed in [("mode", "SIMULATION"), ("run_id", str(uuid4())),
                               ("source_id", str(uuid4())), ("interface_name", "other")]:
            self.assertEqual(self.post("monitoring-sessions", {**self.session, field: changed}).status_code, 409)
        self.assertEqual(MonitoringSession.objects.count(), 1)

    def test_each_record_has_idempotent_retries_and_conflicting_reuse(self):
        for endpoint, data in [("telemetry", self.sample()), ("windows", self.window()), ("capture-status", self.status())]:
            with self.subTest(endpoint=endpoint):
                first = self.post(endpoint, data)
                second = self.post(endpoint, deepcopy(data))
                self.assertEqual((first.status_code, second.status_code), (201, 200))
                self.assertEqual(first.data, second.data)
                self.assertEqual(self.post(endpoint, {**data, "id": str(uuid4())}).status_code, 409)
                if endpoint == "telemetry":
                    changed = {**data, "bytes_sent": 101}
                elif endpoint == "windows":
                    changed = {**data, "flow_count": 1}
                else:
                    changed = {**data, "reason": "changed_reason"}
                self.assertEqual(self.post(endpoint, changed).status_code, 409)

    def test_microsecond_changes_are_not_silently_deduplicated(self):
        data = self.sample()
        data["observed_at"] = (self.start + timedelta(seconds=1, microseconds=1)).isoformat()
        self.assertEqual(self.post("telemetry", data).status_code, 201)
        data["observed_at"] = (self.start + timedelta(seconds=1, microseconds=2)).isoformat()
        self.assertEqual(self.post("telemetry", data).status_code, 409)

    def test_cross_session_mode_run_interface_and_unknown_session_rejected(self):
        for endpoint, data in [("telemetry", self.sample()), ("windows", self.window()), ("capture-status", self.status())]:
            for field, value in [("mode", "SIMULATION"), ("run_id", str(uuid4())),
                                 ("interface_name", "other-interface"), ("session_id", str(uuid4()))]:
                with self.subTest(endpoint=endpoint, field=field):
                    self.assertEqual(self.post(endpoint, {**data, field: value}).status_code, 400)
        self.assertEqual(TelemetrySample.objects.count(), 0)

    def test_new_recovery_session_preserves_run_without_merging_records(self):
        self.assertEqual(self.post("telemetry", self.sample()).status_code, 201)
        recovered = {**self.session, "session_id": str(uuid4()),
                     "started_at": (self.start + timedelta(seconds=10)).isoformat()}
        self.assertEqual(self.post("monitoring-sessions", recovered).status_code, 201)
        data = {**self.sample(), "session_id": recovered["session_id"],
                "observed_at": (self.start + timedelta(seconds=11)).isoformat()}
        self.assertEqual(self.post("telemetry", data).status_code, 201)
        self.assertEqual(len(self.recent("telemetry").data["results"]), 1)

    def test_run_cannot_be_rebound_through_a_new_session(self):
        for field, value in (("source_id", str(uuid4())), ("mode", "SIMULATION"),
                             ("interface_name", "other"), ("observation_profile", "other-profile")):
            with self.subTest(field=field):
                response = self.post("monitoring-sessions", {
                    **self.session, "session_id": str(uuid4()), field: value})
                self.assertEqual(response.status_code, 409)
                self.assertIn("Run ID", str(response.data))
        self.assertEqual(MonitoringSession.objects.count(), 1)

    def test_unknown_and_payload_fields_are_rejected_everywhere(self):
        for endpoint, data in [("monitoring-sessions", self.session), ("telemetry", self.sample()),
                               ("windows", self.window()), ("capture-status", self.status())]:
            for field in ("payload", "raw_packet", "features", "received_at", "payload_digest"):
                with self.subTest(endpoint=endpoint, field=field):
                    self.assertEqual(self.post(endpoint, {**data, field: "not-permitted"}).status_code, 400)

    def test_invalid_sample_preserves_missing_values(self):
        data = self.sample()
        data.update(valid=False, reason="sampling_gap", elapsed_seconds=4,
                    upload_bytes_per_second=None, download_bytes_per_second=None)
        for name in list(data):
            if name.startswith("delta_"):
                data[name] = None
        response = self.post("telemetry", data)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data["upload_bytes_per_second"])
        self.assertIsNone(self.recent("telemetry").data["results"][0]["delta_bytes_sent"])

    def test_sample_validation_rejects_invalid_measurements(self):
        for changes in ({"bytes_sent": -1}, {"bytes_sent": 2**63}, {"bytes_sent": True},
                        {"packets_sent": 1.25}, {"elapsed_seconds": 0}, {"elapsed_seconds": 4},
                        {"upload_bytes_per_second": -1}, {"upload_bytes_per_second": 999},
                        {"upload_bytes_per_second": None}, {"delta_bytes_sent": 101},
                        {"reason": "invalid"}, {"valid": False}, {"valid": "false"},
                        {"measurement_source": "PACKET_METADATA"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post("telemetry", {**self.sample(), **changes}).status_code, 400)

    def test_nan_infinity_and_numeric_overflow_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            data = self.sample()
            data["elapsed_seconds"] = value
            serializer = TelemetrySampleSerializer(data=data)
            self.assertFalse(serializer.is_valid())
        response = self.client.post("/api/v1/telemetry/", '{"elapsed_seconds":1e999}', content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_timestamps_require_timezone_and_preserve_offset_instant(self):
        data = self.sample()
        naive = (self.start + timedelta(seconds=1)).replace(tzinfo=None).isoformat()
        self.assertEqual(self.post("telemetry", {**data, "observed_at": naive}).status_code, 400)
        timestamp = (self.start + timedelta(seconds=1)).astimezone(dt_timezone(timedelta(hours=5, minutes=30)))
        self.assertEqual(self.post("telemetry", {**data, "observed_at": timestamp.isoformat()}).status_code, 201)
        self.assertEqual(TelemetrySample.objects.get().observed_at, timestamp)
        self.assertEqual(self.post("telemetry", data).status_code, 200)

    def test_records_cannot_predate_session(self):
        for endpoint, data in [("telemetry", self.sample()), ("capture-status", self.status())]:
            data["observed_at"] = (self.start - timedelta(seconds=1)).isoformat()
            self.assertEqual(self.post(endpoint, data).status_code, 400)

    def test_partial_window_retains_counts_and_reason(self):
        data = self.window()
        data.update(partial=True, valid=False, reason="shutdown",
                    finalized_at=(self.start + timedelta(seconds=15)).isoformat())
        response = self.post("windows", data)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data["valid"])
        self.assertEqual(response.data["packets"], 3)

    def test_window_conservation_timing_and_quality_validation(self):
        for changes in ({"packets": 4}, {"ip_bytes": 181}, {"udp_packets": 2}, {"outbound_bytes": -1},
                        {"flow_count": 10001}, {"flow_count": 4}, {"partial": True}, {"valid": False},
                        {"dropped": 1}, {"kernel_loss": "zero"},
                        {"end": (self.start + timedelta(seconds=21)).isoformat()},
                        {"finalized_at": (self.start + timedelta(seconds=21)).isoformat()},
                        {"processed_at": (self.start + timedelta(seconds=21)).isoformat()}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post("windows", {**self.window(), **changes}).status_code, 400)

    def test_complete_empty_window_is_observed_zero(self):
        data = self.window()
        for name in ("packets", "ip_bytes", "outbound_packets", "inbound_packets", "outbound_bytes",
                     "inbound_bytes", "tcp_packets", "udp_packets", "flow_count"):
            data[name] = 0
        self.assertEqual(self.post("windows", data).status_code, 201)

    def test_unknown_attribution_or_unsupported_protocol_is_not_complete_coverage(self):
        unknown = {**self.window(), "unknown_packets": 1, "unknown_bytes": 60,
                   "outbound_packets": 1, "outbound_bytes": 60}
        other = {**self.window(), "tcp_packets": 1, "other_packets": 1}
        for data in (unknown, other):
            self.assertEqual(self.post("windows", data).status_code, 400)
        unknown.update(partial=True, valid=False, reason="unknown_direction")
        self.assertEqual(self.post("windows", unknown).status_code, 201)

    def test_status_gap_and_state_consistency(self):
        for changes in ({"valid": True}, {"reason": None}, {"state": "UNKNOWN"},
                        {"monitoring_gap_seconds": -1}, {"recovery_attempts": -1},
                        {"gap_ended_at": (self.start + timedelta(seconds=1)).isoformat()}):
            self.assertEqual(self.post("capture-status", {**self.status(), **changes}).status_code, 400)
        data = self.status()
        data.update(state="RUNNING", valid=True, reason="interface_recovered",
                    observed_at=(self.start + timedelta(seconds=7)).isoformat(),
                    gap_ended_at=(self.start + timedelta(seconds=7)).isoformat(), monitoring_gap_seconds=5)
        self.assertEqual(self.post("capture-status", data).status_code, 201)

    def test_recent_reads_are_filtered_bounded_and_paginated(self):
        for seconds in range(1, 5):
            data = {**self.sample(), "observed_at": (self.start + timedelta(seconds=seconds)).isoformat()}
            self.assertEqual(self.post("telemetry", data).status_code, 201)
        first = self.recent("telemetry", limit=2)
        self.assertEqual(len(first.data["results"]), 2)
        second = self.client.get(first.data["next"])
        self.assertEqual(len(second.data["results"]), 2)
        self.assertFalse({r["id"] for r in first.data["results"]} & {r["id"] for r in second.data["results"]})
        self.assertEqual(self.recent("telemetry", limit=201).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/telemetry/").status_code, 400)
        self.assertEqual(self.recent("telemetry", mode="REPLAY").data["results"], [])
        self.assertEqual(self.recent("telemetry", session_id=str(uuid4())).data["results"], [])

    def test_old_replay_and_future_observations_are_not_recent(self):
        for timestamp in (self.start - timedelta(days=3), timezone.now() + timedelta(days=1)):
            self.session.update(session_id=str(uuid4()), run_id=str(uuid4()), mode="REPLAY", started_at=(timestamp - timedelta(seconds=1)).isoformat())
            self.assertEqual(self.post("monitoring-sessions", self.session).status_code, 201)
            self.assertEqual(self.post("telemetry", {**self.sample(), "observed_at": timestamp.isoformat()}).status_code, 201)
            self.assertEqual(self.recent("telemetry", mode="REPLAY").data["results"], [])

    def test_only_get_and_post_are_exposed(self):
        for method in (self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(method("/api/v1/telemetry/", {}, format="json").status_code, 403)

    def test_local_boundary_blocks_remote_browser_origins_and_spoofed_proxy_headers(self):
        for kwargs in ({"REMOTE_ADDR": "192.0.2.1"}, {"HTTP_ORIGIN": "https://example.com"},
                       {"HTTP_SEC_FETCH_SITE": "cross-site"},
                       {"REMOTE_ADDR": "192.0.2.1", "HTTP_X_FORWARDED_FOR": "127.0.0.1"}):
            self.assertEqual(self.client.get("/api/v1/health/", **kwargs).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/health/", HTTP_HOST="example.com").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/health/")["Cache-Control"], "no-store")

    def test_body_limit_and_non_json_requests(self):
        with override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=20):
            response = self.client.post("/api/v1/telemetry/", "x" * 21, content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.client.post("/api/v1/telemetry/", "x", content_type="text/plain").status_code, 415)

    def test_database_constraints_defend_core_window_invariants(self):
        self.assertEqual(self.post("windows", self.window()).status_code, 201)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TrafficWindow.objects.update(ip_bytes=999)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MonitoringSession.objects.update(mode="INVALID")

    def test_cleanup_is_bounded_and_preserves_fresh_data_and_session_manifests(self):
        serializer = TelemetrySampleSerializer(data=self.sample())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        attrs = dict(serializer.validated_data)
        attrs.pop("id")
        records = [TelemetrySample(**{**attrs, "observed_at": self.start + timedelta(seconds=i)},
                                   payload_digest="0" * 64) for i in range(1002)]
        TelemetrySample.objects.bulk_create(records)
        TelemetrySample.objects.update(received_at=timezone.now() - timedelta(days=2))
        recent = records[-1]
        TelemetrySample.objects.filter(pk=recent.pk).update(received_at=timezone.now())
        call_command("prune_telemetry", stdout=StringIO())
        self.assertEqual(TelemetrySample.objects.count(), 2)
        self.assertTrue(TelemetrySample.objects.filter(pk=recent.pk).exists())
        self.assertEqual(MonitoringSession.objects.count(), 1)
