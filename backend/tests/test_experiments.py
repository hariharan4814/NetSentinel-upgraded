"""Synthetic fixtures only: job authorization, leases, bounds and provenance."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from unittest.mock import patch
from django.conf import settings
from django.db import OperationalError
from django.test import TestCase, SimpleTestCase, RequestFactory
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from experiments.models import ExperimentJob as Job
from experiments import services, validation
from lab.contracts import validate_config
from common.middleware import LocalOnlyMiddleware


def fixture_result():
    """A deliberately tiny structurally valid result, never a reported ML run."""
    return {
        "schema_version": "lab-result-v1", "mode": "SIMULATION",
        "generated_at": "2026-10-05T00:00:00+00:00", "config": validate_config({}),
        "dataset": {"sha256": "a" * 64, "total_windows": 3, "valid_windows": 3,
                    "unscored_windows": 0, "event_count": 12,
                    "feature_names": list(validation.FEATURES), "splits": {
                        key: {"run_ids": [key], "windows": 1} for key in ("train", "validation", "test")}},
        "models": [], "references": {key: {"median": 1, "p05": 0, "p95": 2, "p99": 3} for key in validation.FEATURES},
        "classification": [], "anomaly": {"threshold": 0.5, "precision": None, "recall": None,
            "false_positive_rate": 0, "average_precision": None, "false_alerts_per_hour": 0,
            "scored_windows": 1, "unscored_windows": 0},
        "timeline": [{"id": "window-1", "run_id": "test", "window_index": 0,
            "time_seconds": 0, "truth_family": "routine", "challenge": False,
            "features": {key: 0 for key in validation.FEATURES}, "predicted_family": "routine",
            "class_probability": 0.8, "anomaly_score": 0.3, "anomalous": False}],
        "explanations": [], "performance": {key: 0 for key in ("generation_seconds", "training_seconds",
            "evaluation_seconds", "total_seconds", "inference_p50_ms", "inference_p95_ms", "peak_rss_bytes")},
        "limitations": ["Synthetic schema test, not model evaluation."],
        "displayed_windows": 1, "total_test_windows": 1,
    }


class ExperimentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def request(self, method, path, data=None, scope="lab", **headers):
        token = {"lab": settings.NETSENTINEL_LAB_TOKEN, "worker": settings.NETSENTINEL_LAB_WORKER_TOKEN,
                 "read": settings.NETSENTINEL_READ_TOKEN, "ingest": settings.NETSENTINEL_INGEST_TOKEN}[scope]
        return self.client.generic(method, "/api/v1/lab/" + path,
            json.dumps(data or {}), content_type="application/json", HTTP_HOST="localhost",
            HTTP_AUTHORIZATION="Bearer " + token, **headers)

    def create(self):
        response = self.request("POST", "jobs/", {"config": {}})
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def claim(self):
        response = self.request("POST", "worker/claim/", scope="worker")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_scopes_missing_credentials_and_browser_origins(self):
        self.assertEqual(self.client.get("/api/v1/lab/jobs/", HTTP_HOST="localhost").status_code, 401)
        for scope in ("read", "ingest", "worker"):
            self.assertEqual(self.request("POST", "jobs/", {"config": {}}, scope).status_code, 403)
        for scope in ("lab", "read", "ingest"):
            self.assertEqual(self.request("POST", "worker/claim/", scope=scope).status_code, 403)
        self.assertEqual(self.request("GET", "jobs/", scope="read").status_code, 200)
        self.assertEqual(self.request("GET", "jobs/", scope="worker").status_code, 403)
        self.assertEqual(self.request("POST", "jobs/", {"config": {}}, HTTP_ORIGIN="http://localhost").status_code, 403)

    def test_database_failure_is_explicit_and_redacts_details(self):
        with patch("experiments.services.QueueGuard.objects.filter", side_effect=OperationalError("private-database-password")):
            response = self.request("GET", "jobs/", scope="read")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"error": "database_unavailable"})

    def test_input_config_query_and_duplicate_keys(self):
        for config in ({"seed": True}, {"seed": -1}, {"mode": "LIVE"}, {"noise": 5}, {"runs_per_family": 100}, {"path": "C:/secret"}):
            self.assertEqual(self.request("POST", "jobs/", {"config": config}).status_code, 400)
        self.assertEqual(self.request("POST", "jobs/", {"config": {}, "unknown": 1}).status_code, 400)
        self.assertEqual(self.request("GET", "jobs/?limit=100", scope="read").status_code, 400)
        for raw in ('{"config":{},"config":{"seed":3}}', '{"config":{"noise":NaN}}', '[' * 1001 + ']' * 1001):
            response = self.client.post("/api/v1/lab/jobs/", raw, content_type="application/json",
                HTTP_HOST="localhost", HTTP_AUTHORIZATION="Bearer " + settings.NETSENTINEL_LAB_TOKEN)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Job.objects.count(), 0)

    def test_queue_bound_and_single_claim_and_lease_hash(self):
        for _ in range(4):
            self.create()
        self.assertEqual(self.request("POST", "jobs/", {"config": {}}).status_code, 429)
        claim = self.claim()
        self.assertEqual(claim["job"]["status"], "RUNNING")
        job = Job.objects.get(id=claim["job"]["id"])
        self.assertEqual(job.lease_digest, hashlib.sha256(claim["lease_token"].encode()).hexdigest())
        self.assertNotIn("lease_digest", claim["job"])
        self.assertEqual(self.claim(), {"job": None})
        self.create()  # one running plus four queued is the bounded limit.

    def test_restart_can_read_persisted_jobs_and_expired_lease_fails(self):
        self.create()
        old = self.claim()
        Job.objects.filter(id=old["job"]["id"]).update(lease_expires_at=timezone.now() - timedelta(seconds=1))
        response = self.request("GET", "jobs/", scope="read").json()
        self.assertEqual(response["jobs"][0]["status"], "FAILED")
        body = {"lease_token": old["lease_token"], "stage": "training"}
        self.assertEqual(self.request("POST", f"worker/{old['job']['id']}/heartbeat/", body, "worker").status_code, 409)
        self.assertEqual(self.claim(), {"job": None})

    def test_cancellation_of_queued_and_running_jobs(self):
        queued = self.create()
        cancelled = self.request("POST", f"jobs/{queued['id']}/cancel/").json()
        self.assertEqual(cancelled["status"], "CANCELLED")
        self.create()
        claim = self.claim()
        job_id, token = claim["job"]["id"], claim["lease_token"]
        self.request("POST", f"jobs/{job_id}/cancel/")
        progress = self.request("POST", f"worker/{job_id}/heartbeat/", {"lease_token": token, "stage": "training"}, "worker")
        self.assertEqual(progress.json(), {"cancel_requested": True})
        finished = self.request("POST", f"worker/{job_id}/finish/", {"lease_token": token, "status": "SUCCEEDED", "result": fixture_result()}, "worker")
        self.assertEqual(finished.json()["status"], "CANCELLED")
        self.assertIsNone(Job.objects.get(id=job_id).result)

    def test_progress_bound_lease_ownership_and_unknown_fields(self):
        self.create()
        claim = self.claim()
        path = f"worker/{claim['job']['id']}/heartbeat/"
        for extra in ({"completed": 2, "total": 1}, {"completed": 1}, {"completed": True}, {"stage": "private\ntext"}, {"command": "invoke"}):
            body = {"lease_token": claim["lease_token"], "stage": "training", **extra}
            self.assertEqual(self.request("POST", path, body, "worker").status_code, 400)
        self.assertEqual(self.request("POST", path, {"lease_token": "b" * 64, "stage": "training"}, "worker").status_code, 409)

    def test_finish_retains_result_only_in_detail_and_is_not_replayable(self):
        self.create()
        claim = self.claim()
        path = f"worker/{claim['job']['id']}/finish/"
        body = {"lease_token": claim["lease_token"], "status": "SUCCEEDED", "result": fixture_result()}
        self.assertEqual(self.request("POST", path, body, "worker").status_code, 200)
        self.assertEqual(self.request("POST", path, body, "worker").status_code, 409)
        self.assertNotIn("result", self.request("GET", "jobs/", scope="read").json()["jobs"][0])
        detail = self.request("GET", f"jobs/{claim['job']['id']}/", scope="read").json()
        self.assertEqual(detail["result"]["mode"], "SIMULATION")
        self.assertNotIn("lease_token", detail)
        self.assertEqual(self.request("POST", f"jobs/{claim['job']['id']}/cancel/").json()["status"], "SUCCEEDED")

    def test_result_config_mismatch_and_arbitrary_error_redaction(self):
        self.create()
        claim = self.claim()
        path = f"worker/{claim['job']['id']}/finish/"
        value = fixture_result()
        value["config"]["seed"] = 15
        self.assertEqual(self.request("POST", path, {"lease_token": claim["lease_token"], "status": "SUCCEEDED", "result": value}, "worker").status_code, 409)
        response = self.request("POST", path, {"lease_token": claim["lease_token"], "status": "FAILED", "error": "synthetic-secret-token C:/private/path"}, "worker")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("synthetic-secret", response.content.decode())
        self.assertNotIn("C:/private", Job.objects.get(id=claim["job"]["id"]).error)

    def test_retention_prunes_oldest_finished_and_preserves_active(self):
        for _ in range(20):
            Job.objects.create(config=validate_config({}), status="CANCELLED")
        oldest = Job.objects.order_by("created_at", "id").first().id
        first = self.create()
        self.assertEqual(Job.objects.count(), 20)
        self.assertFalse(Job.objects.filter(id=oldest).exists())
        self.claim()
        for _ in range(4):
            self.create()
        self.assertEqual(Job.objects.count(), 20)
        self.assertEqual(Job.objects.get(id=first["id"]).status, "RUNNING")


class ResultContractTests(SimpleTestCase):
    def test_valid_synthetic_structure(self):
        self.assertEqual(validation.result(fixture_result())["mode"], "SIMULATION")

    def test_provenance_nonfinite_unknown_fields_missing_data_and_leakage(self):
        changes = [
            lambda r: r.update(mode="LIVE"),
            lambda r: r.update(path="C:/secret"),
            lambda r: r["performance"].update(total_seconds=float("inf")),
            lambda r: r["anomaly"].update(precision=1.1),
            lambda r: r["dataset"]["splits"]["test"].update(run_ids=["train"]),
            lambda r: r["timeline"][0].update(features=None),
            lambda r: r.update(displayed_windows=20),
            lambda r: r.update(generated_at="2026-10-05T00:00:00"),
            lambda r: r["references"][validation.FEATURES[0]].update(p05=10),
            lambda r: r["timeline"][0].update(anomalous=1),
            lambda r: r["performance"].update(total_seconds=10 ** 1000),
        ]
        for change in changes:
            value = deepcopy(fixture_result())
            change(value)
            with self.subTest(change=change), self.assertRaises(ValidationError):
                validation.result(value)

    def test_authenticated_finish_has_larger_cap_only(self):
        factory = RequestFactory()
        middleware = LocalOnlyMiddleware(lambda request: JsonResponse({"bytes": len(request.body)}))
        def call(path, token, size):
            return middleware(factory.post(path, b"x" * size, content_type="application/json",
                HTTP_HOST="localhost", HTTP_AUTHORIZATION="Bearer " + token))
        finish = "/api/v1/lab/worker/00000000-0000-4000-8000-000000000000/finish/"
        self.assertEqual(call(finish, settings.NETSENTINEL_LAB_WORKER_TOKEN, 100000).status_code, 200)
        self.assertEqual(call(finish, settings.NETSENTINEL_LAB_WORKER_TOKEN, 4 * 1024 * 1024 + 1).status_code, 413)
        self.assertEqual(call(finish, settings.NETSENTINEL_READ_TOKEN, 100000).status_code, 403)
        self.assertEqual(call("/api/v1/lab/worker/claim/", settings.NETSENTINEL_LAB_WORKER_TOKEN, 100000).status_code, 413)
