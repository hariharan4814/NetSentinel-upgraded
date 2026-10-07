"""Synthetic aggregate fixtures, isolated SQLite database; no LIVE evidence claims."""
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4
from django.utils import timezone
from rest_framework.test import APITestCase
from detection.contract import FEATURE_NAMES, PARAMETERS, profile, eligible
from detection.models import ModelVersion, AnomalyResult
from telemetry.models import TrafficWindow
from .support import ScopedFixtureClient


class DetectionTests(APITestCase):
    client_class = ScopedFixtureClient
    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"
        start = (timezone.now() - timedelta(minutes=3)).replace(second=0, microsecond=0)
        self.session = {"session_id": str(uuid4()), "source_id": str(uuid4()), "run_id": str(uuid4()),
                        "mode": "SIMULATION", "interface_name": "fixture", "observation_profile": "test-only",
                        "started_at": start.isoformat(), "schema_version": "backend-v1"}
        self.assertEqual(self.post("monitoring-sessions", self.session).status_code, 201)
        self.window = {k: self.session[k] for k in ("session_id", "run_id", "mode", "interface_name")}
        self.window.update({"id": str(uuid4()), "start": start.isoformat(), "end": (start + timedelta(seconds=10)).isoformat(),
                            "finalized_at": (start + timedelta(seconds=12)).isoformat(), "processed_at": (start + timedelta(seconds=12)).isoformat(),
                            "measurement_source": "PACKET_METADATA", "schema_version": "backend-window-v1", "valid": True,
                            "partial": False, "reason": None, "packets": 2, "ip_bytes": 120, "outbound_packets": 2,
                            "inbound_packets": 0, "outbound_bytes": 120, "inbound_bytes": 0, "tcp_packets": 2,
                            "udp_packets": 0, "unknown_packets": 0, "unknown_bytes": 0, "other_packets": 0,
                            "flow_count": 1, "dropped": 0, "kernel_loss": "unknown", "feature_schema_version": "host-v1",
                            "features": dict(zip(FEATURE_NAMES, [.2, 12, 1, 1, .5, 0, 60])),
                            "capture_context": {"capture_interface": "fixture-guid", "interface_index": 1,
                                                "filter": "ip or ip6", "promiscuous": False,
                                                "local_addresses": ["192.0.2.1"], "flow_schema_version": "phase1b-flow-v1"}})
        self.manifest = {
            "id": str(uuid4()), "schema": "iforest-host-v1", "feature_schema_version": "host-v1",
            "feature_order": list(FEATURE_NAMES), "parameters": PARAMETERS, "preprocessing": "none",
            "score_semantics": "negative_score_samples; higher means more unusual; not attack probability",
            "threshold": .6, "threshold_policy": "calibration_p99_higher_strict_greater_v1",
            "profile": profile(self.session, self.window), "trained_at": start.isoformat(), "sample_count": 300,
            "dataset_sha256": "1" * 64, "review_sha256": "2" * 64, "artifact_sha256": "3" * 64,
            "sklearn_version": "1.9.0", "numpy_version": "2.4.6", "python_version": "3.11.0", "joblib_version": "1.6.0",
            "training_evaluation_seconds": 1, "rss_after_bytes": 1000,
            "splits": {name: {"count": count, "run_ids": [str(uuid4()) for _ in range(runs)],
                              "first_start": (start - timedelta(days=6 - i)).isoformat(),
                              "last_end": (start - timedelta(days=6 - i) + timedelta(seconds=count * 10)).isoformat(),
                              "sha256": "4" * 64} for i, (name, count, runs) in enumerate((("train", 300, 3), ("calibration", 100, 1), ("test", 100, 1)))},
            "evaluation": {"calibration_scores": {k: .5 for k in ("min", "p50", "p95", "p99", "max")},
                           "held_out_scores": {k: .5 for k in ("min", "p50", "p95", "p99", "max")},
                           "held_out_anomalous": 0, "held_out_count": 100, "reviewed_normal_flag_fraction": 0,
                           "per_run": [], "limitations": "Synthetic metadata-only test, no trained LIVE model."}}
        self.manifest["evaluation"]["per_run"] = [{"run_id": self.manifest["splits"]["test"]["run_ids"][0],
                                                   "windows": 100, "anomalous": 0, "anomalous_per_observed_hour": 0}]

    def post(self, endpoint, data):
        return self.client.post(f"/api/v1/{endpoint}/", data, format="json")

    def model(self):
        return {"id": self.manifest["id"], "manifest": self.manifest}

    def result(self):
        return {**{k: self.session[k] for k in ("session_id", "run_id", "mode", "interface_name")},
                "id": str(uuid4()), "window_id": self.window["id"], "model_version_id": self.manifest["id"],
                "observed_at": self.window["end"], "scored_at": timezone.now().isoformat(), "anomaly_score": .5, "label": "NORMAL"}

    def ingest(self):
        self.assertEqual(self.post("windows", self.window).status_code, 201)
        response = self.post("model-versions", self.model())
        self.assertEqual(response.status_code, 201, response.data)

    def test_seven_feature_persistence_retry_conflict(self):
        self.assertEqual(self.post("windows", self.window).status_code, 201)
        self.assertEqual(self.post("windows", self.window).status_code, 200)
        self.window["features"]["tcp_syn_fraction"] = 1
        self.assertEqual(self.post("windows", self.window).status_code, 409)
        self.assertEqual(TrafficWindow.objects.get().features["tcp_syn_fraction"], .5)

    def test_legacy_readable_but_ineligible(self):
        legacy = {k: v for k, v in self.window.items() if k not in ("features", "feature_schema_version", "capture_context")}
        response = self.post("windows", legacy)
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["features"])
        with self.assertRaises(ValueError):
            eligible(dict(response.data))
        self.assertEqual(self.post("model-versions", self.model()).status_code, 201)
        self.assertEqual(self.post("anomaly-results", self.result()).status_code, 400)

    def test_partial_invalid_and_missing_features_rejected(self):
        for changes in ({"partial": True, "valid": False, "reason": "partial"}, {"valid": False},
                        {"features": {}}, {"feature_schema_version": "wrong"}, {"capture_context": None}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post("windows", self.window | changes).status_code, 400)

    def test_unknown_payload_and_missing_syn_rejected(self):
        self.assertEqual(self.post("windows", self.window | {"packet_payload": "bad"}).status_code, 400)
        del self.window["features"]["tcp_syn_fraction"]
        self.assertEqual(self.post("windows", self.window).status_code, 400)

    def test_model_metadata_retry_conflict(self):
        self.assertEqual(self.post("model-versions", self.model()).status_code, 201)
        self.assertEqual(self.post("model-versions", self.model()).status_code, 200)
        self.manifest["threshold"] = .7
        self.assertEqual(self.post("model-versions", self.model()).status_code, 409)
        self.assertEqual(ModelVersion.objects.count(), 1)

    def test_model_wrong_order_schema_missing_metadata(self):
        for changes in ({"feature_order": list(reversed(FEATURE_NAMES))}, {"schema": "wrong"}, {"feature_schema_version": "wrong"}):
            payload = self.model() | {"manifest": self.manifest | changes}
            self.assertEqual(self.post("model-versions", payload).status_code, 400)
        del self.manifest["trained_at"]
        self.assertEqual(self.post("model-versions", self.model()).status_code, 400)

    def test_anomaly_result_retry_conflict_and_provenance(self):
        self.ingest()
        result = self.result()
        self.assertEqual(self.post("anomaly-results", result).status_code, 201)
        self.assertEqual(self.post("anomaly-results", result).status_code, 200)
        self.assertEqual(self.post("anomaly-results", result | {"id": str(uuid4())}).status_code, 409)
        self.assertEqual(self.post("anomaly-results", result | {"anomaly_score": .4}).status_code, 409)
        self.assertEqual(AnomalyResult.objects.count(), 1)
        response = self.client.get("/api/v1/anomaly-results/", {"session_id": self.session["session_id"], "mode": "SIMULATION"})
        self.assertEqual(response.data["results"][0]["run_id"], self.session["run_id"])

    def test_scoring_identity_and_vocabulary(self):
        self.ingest()
        for changes in ({"mode": "LIVE"}, {"run_id": str(uuid4())}, {"window_id": str(uuid4())},
                        {"label": "ATTACK"}, {"label": "MALWARE"}, {"label": "INTRUSION"}, {"label": "EXFILTRATION"},
                        {"label": "ANOMALOUS"}, {"anomaly_score": 2}, {"scored_at": "2026-01-01T00:00:00"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post("anomaly-results", self.result() | changes).status_code, 400)

    def test_model_mode_cannot_cross_to_live(self):
        self.manifest["profile"]["mode"] = "LIVE"
        self.ingest()
        self.assertEqual(self.post("anomaly-results", self.result()).status_code, 400)

    def test_scoped_reads(self):
        self.ingest()
        url = "/api/v1/model-versions/"
        query = {"id": self.manifest["id"], "source_id": self.session["source_id"], "mode": "SIMULATION"}
        self.assertEqual(self.client.get(url, query).status_code, 200)
        self.assertEqual(self.client.get(url, query | {"mode": "LIVE"}).status_code, 404)
        self.assertEqual(self.client.get(url, query | {"source_id": str(uuid4())}).status_code, 404)
        self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/anomaly-results/").status_code, 400)

    def test_explainability_normal_and_anomalous(self):
        from detection.explain import explain_anomaly
        # 1. Normal window explanation is neutral
        normal_res = explain_anomaly(self.window["features"], label="NORMAL")
        self.assertEqual(normal_res["explanation"], "Within learned baseline range")
        self.assertEqual(normal_res["deviating_features"], [])

        # 2. Anomalous window with specific burst rates identifies deviating features
        anomalous_features = {
            "packets_per_second": 850.0,         # > p95 (80)
            "ip_bytes_per_second": 700000.0,     # > p95 (60000)
            "outbound_byte_fraction": 0.5,       # <= p95 (0.95)
            "unique_remote_peers": 40,           # > p95 (10)
            "tcp_syn_fraction": 0.02,            # <= p95 (0.15)
            "udp_fraction": 0.05,                # <= p95 (0.50)
            "mean_ip_packet_bytes": 800.0,       # <= p95 (1200)
        }
        anom_res = explain_anomaly(anomalous_features, label="ANOMALOUS")
        self.assertIn("throughput", anom_res["explanation"])
        self.assertIn("packet rate", anom_res["explanation"])
        self.assertIn("remote peer", anom_res["explanation"])
        self.assertEqual(set(anom_res["deviating_features"]), {"ip_bytes_per_second", "packets_per_second", "unique_remote_peers"})

        # 3. Strictly neutral vocabulary: no attack, malware, threat or intrusion words
        for bad_word in ("attack", "malware", "threat", "intrusion", "exfiltration", "malicious"):
            self.assertNotIn(bad_word, anom_res["explanation"].lower())
            self.assertNotIn(bad_word, normal_res["explanation"].lower())

    def test_anomaly_api_response_includes_explanation(self):
        self.ingest()
        result = self.result()
        self.assertEqual(self.post("anomaly-results", result).status_code, 201)
        response = self.client.get("/api/v1/anomaly-results/", {"session_id": self.session["session_id"], "mode": "SIMULATION"})
        self.assertEqual(response.status_code, 200)
        item = response.data["results"][0]
        self.assertIn("explanation", item)
        self.assertIn("deviating_features", item)
        self.assertIn("threshold", item)
        self.assertEqual(item["threshold"], self.manifest["threshold"])
        self.assertEqual(item["explanation"], "Within learned baseline range")
        self.assertEqual(item["deviating_features"], [])
