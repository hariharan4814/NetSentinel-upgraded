"""Database-serialized state machine for PostgreSQL or explicit lab-only SQLite.

The SQLite guard UPDATE must be the first statement inside the transaction: it
acquires the database write lock before reading queue state across processes.
"""
from datetime import timedelta
import hashlib
import hmac
import secrets
from contextlib import contextmanager
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound
from .models import ExperimentJob as Job, QueueGuard

LEASE_SECONDS = 30
MAX_QUEUED = 4
MAX_RETAINED = 20
LOCK_ID = 0x4E534C41424A4F42
FINAL = (Job.Status.SUCCEEDED, Job.Status.FAILED, Job.Status.CANCELLED)


class StateConflict(APIException):
    status_code = 409
    default_detail = "Job is no longer owned by this worker or has already finished."


class QueueFull(APIException):
    status_code = 429
    default_detail = "Four experiments are already waiting. Wait for a job or cancel one."


@contextmanager
def locked():
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [LOCK_ID])
        elif connection.vendor == "sqlite":
            if QueueGuard.objects.filter(id=1).update(revision=0) != 1:
                raise StateConflict("Queue guard is missing; apply experiment migrations.")
        expire()
        yield


def expire():
    now = timezone.now()
    Job.objects.filter(status=Job.Status.RUNNING, lease_expires_at__lte=now).update(
        status=Job.Status.FAILED, stage="interrupted", updated_at=now,
        error="Worker lease expired; this experiment was interrupted. Start a new run.",
        lease_digest="", lease_expires_at=None, completed=None, total=None)


def serialize(job, *, include_result=False):
    value = {key: getattr(job, key) for key in (
        "status", "stage", "config", "cancel_requested", "completed", "total", "error")}
    value.update(id=str(job.id), created_at=job.created_at.isoformat(), updated_at=job.updated_at.isoformat())
    if include_result and job.status == Job.Status.SUCCEEDED:
        value["result"] = job.result
    return value


def create(config):
    with locked():
        if Job.objects.filter(status=Job.Status.QUEUED).count() >= MAX_QUEUED:
            raise QueueFull()
        excess = max(0, Job.objects.count() - MAX_RETAINED + 1)
        if excess:
            ids = list(Job.objects.filter(status__in=FINAL).order_by("created_at", "id").values_list("id", flat=True)[:excess])
            Job.objects.filter(id__in=ids).delete()
        return serialize(Job.objects.create(config=config))


def get_job(job_id):
    try:
        return Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        raise NotFound("Experiment not found or no longer retained.") from None


def listing():
    with locked():
        return [serialize(job) for job in Job.objects.all()[:MAX_RETAINED]]


def detail(job_id):
    with locked():
        return serialize(get_job(job_id), include_result=True)


def cancel(job_id):
    with locked():
        job = get_job(job_id)
        if job.status == Job.Status.QUEUED:
            job.status, job.stage = Job.Status.CANCELLED, "cancelled"
            job.cancel_requested = True
        elif job.status == Job.Status.RUNNING:
            job.cancel_requested = True
        else:
            return serialize(job)  # Idempotent: never rewrite a finished result.
        job.save()
        return serialize(job)


def claim():
    with locked():
        if Job.objects.filter(status=Job.Status.RUNNING).exists():
            return {"job": None}
        job = Job.objects.filter(status=Job.Status.QUEUED).order_by("created_at", "id").first()
        if job is None:
            return {"job": None}
        token = secrets.token_hex(32)
        job.status, job.stage = Job.Status.RUNNING, "starting"
        job.lease_digest = hashlib.sha256(token.encode()).hexdigest()
        job.lease_expires_at = timezone.now() + timedelta(seconds=LEASE_SECONDS)
        job.save()
        return {"job": serialize(job), "lease_token": token}


def owned(job_id, token):
    job = get_job(job_id)
    digest = hashlib.sha256(token.encode()).hexdigest()
    if job.status != Job.Status.RUNNING or not hmac.compare_digest(job.lease_digest, digest):
        raise StateConflict()
    return job


def heartbeat(job_id, token, stage, completed, total):
    with locked():
        job = owned(job_id, token)
        job.stage, job.completed, job.total = stage, completed, total
        job.lease_expires_at = timezone.now() + timedelta(seconds=LEASE_SECONDS)
        job.save()
        return {"cancel_requested": job.cancel_requested}


def finish(job_id, token, status, result=None, error=""):
    with locked():
        job = owned(job_id, token)
        if result is not None and result["config"] != job.config:
            raise StateConflict("Result configuration does not match the queued experiment.")
        if job.cancel_requested:
            status, result, error = Job.Status.CANCELLED, None, ""
        job.status, job.stage, job.result, job.error = status, status.lower(), result, error
        job.completed, job.total = None, None
        job.lease_digest, job.lease_expires_at = "", None
        job.save()
        return serialize(job)
