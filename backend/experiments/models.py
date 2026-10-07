"""Bounded simulation jobs; no model artifacts or LIVE data in these rows."""
import uuid
from django.db import models


class QueueGuard(models.Model):
    """Singleton row used to acquire SQLite's database write lock before reads."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    revision = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="lab_single_guard")]


class ExperimentJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    stage = models.CharField(max_length=48, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    config = models.JSONField()
    cancel_requested = models.BooleanField(default=False)
    completed = models.PositiveIntegerField(null=True)
    total = models.PositiveIntegerField(null=True)
    error = models.CharField(max_length=200, blank=True, default="")
    result = models.JSONField(null=True)
    lease_digest = models.CharField(max_length=64, blank=True, default="")
    lease_expires_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [models.Index(fields=["status", "created_at"], name="lab_status_created_idx")]
        constraints = [
            models.CheckConstraint(condition=models.Q(status__in=["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"]), name="lab_known_status"),
            models.CheckConstraint(condition=(models.Q(status="SUCCEEDED", result__isnull=False) | (~models.Q(status="SUCCEEDED") & models.Q(result__isnull=True))), name="lab_result_on_success"),
            models.CheckConstraint(condition=(models.Q(completed__isnull=True) | models.Q(total__isnull=True) | models.Q(completed__lte=models.F("total"))), name="lab_progress_bounded"),
            models.UniqueConstraint(fields=["status"], condition=models.Q(status="RUNNING"), name="lab_single_running"),
        ]
