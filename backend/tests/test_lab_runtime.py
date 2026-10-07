"""Real temporary SQLite runtime processes; no PostgreSQL or private data."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from django.test import SimpleTestCase


class StandaloneLabTests(SimpleTestCase):
    def test_persistent_runtime_concurrent_admission_and_claim(self):
        with tempfile.TemporaryDirectory(prefix="netsentinel-lab-test-") as temporary:
            environment = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.lab_settings",
                           "DJANGO_SECRET_KEY": secrets.token_hex(32),
                           "NETSENTINEL_LAB_DATABASE_PATH": str(Path(temporary) / "jobs.sqlite3")}
            for name in ("NETSENTINEL_READ_TOKEN", "NETSENTINEL_LAB_TOKEN", "NETSENTINEL_LAB_WORKER_TOKEN"):
                environment[name] = secrets.token_hex(32)
            first = '''
import django
django.setup()
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from django.urls import resolve, Resolver404
from experiments import services
from experiments.models import ExperimentJob, QueueGuard
from lab.contracts import validate_config
assert settings.INSTALLED_APPS == ["rest_framework", "experiments"]
assert not settings.NETSENTINEL_INGEST_TOKEN and not settings.NETSENTINEL_MODEL_TOKEN
for route in ("/api/v1/telemetry/", "/api/v1/model-versions/", "/api/v1/windows/"):
    try:
        resolve(route)
        raise AssertionError("research route present")
    except Resolver404:
        pass
call_command("migrate", verbosity=0)
assert QueueGuard.objects.count() == 1
barrier = Barrier(12)
def submit(_):
    try:
        barrier.wait(timeout=20)
        services.create(validate_config({}))
        return "created"
    except services.QueueFull:
        return "full"
    finally:
        connections.close_all()
with ThreadPoolExecutor(max_workers=12) as executor:
    outcomes = list(executor.map(submit, range(12)))
assert outcomes.count("created") == 4, outcomes
assert outcomes.count("full") == 8, outcomes
barrier = Barrier(8)
def claim(_):
    try:
        barrier.wait(timeout=20)
        return services.claim()["job"] is not None
    finally:
        connections.close_all()
with ThreadPoolExecutor(max_workers=8) as executor:
    claims = list(executor.map(claim, range(8)))
assert sum(claims) == 1, claims
assert ExperimentJob.objects.filter(status="RUNNING").count() == 1
assert ExperimentJob.objects.filter(status="QUEUED").count() == 3
print("SQLite admission and claim concurrency passed")
'''
            second = '''
import django
django.setup()
from datetime import timedelta
from django.utils import timezone
from experiments import services
from experiments.models import ExperimentJob
assert ExperimentJob.objects.count() == 4
assert ExperimentJob.objects.filter(status="RUNNING").count() == 1
ExperimentJob.objects.filter(status="RUNNING").update(lease_expires_at=timezone.now()-timedelta(seconds=1))
assert len(services.listing()) == 4
assert ExperimentJob.objects.filter(status="FAILED", stage="interrupted").count() == 1
assert services.claim()["job"] is not None
print("Fresh-process persistence and recovery passed")
'''
            for code in (first, second):
                result = subprocess.run([sys.executable, "-c", code], env=environment,
                                        cwd=Path(__file__).resolve().parents[1],
                                        capture_output=True, text=True, timeout=50)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
