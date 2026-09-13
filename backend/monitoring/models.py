from uuid import uuid4
from django.db import models
from django.db.models import Q


class Mode(models.TextChoices):
    LIVE = "LIVE"
    SIMULATION = "SIMULATION"
    REPLAY = "REPLAY"


class MonitoringSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    source_id = models.UUIDField()
    run_id = models.UUIDField(db_index=True)
    interface_name = models.CharField(max_length=255)
    mode = models.CharField(max_length=10, choices=Mode.choices)
    started_at = models.DateTimeField()
    observation_profile = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=40, default="backend-v1")
    received_at = models.DateTimeField(auto_now_add=True)
    payload_digest = models.CharField(max_length=64, editable=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(mode__in=Mode.values), name="session_mode_valid")]


class SessionRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    session = models.ForeignKey(MonitoringSession, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    payload_digest = models.CharField(max_length=64, editable=False)

    class Meta:
        abstract = True


class CaptureStatus(SessionRecord):
    class State(models.TextChoices):
        RUNNING = "RUNNING"
        INTERFACE_LOST = "INTERFACE_LOST"
        RECOVERING = "RECOVERING"
        STOPPED = "STOPPED"

    observed_at = models.DateTimeField()
    state = models.CharField(max_length=20, choices=State.choices)
    valid = models.BooleanField()
    reason = models.CharField(max_length=255, null=True, blank=True)
    loss_started_at = models.DateTimeField(null=True, blank=True)
    gap_ended_at = models.DateTimeField(null=True, blank=True)
    monitoring_gap_seconds = models.FloatField(default=0)
    recovery_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "observed_at"], name="status_session_observed_unique"),
            models.CheckConstraint(condition=Q(state__in=["RUNNING", "INTERFACE_LOST", "RECOVERING", "STOPPED"]), name="status_state_valid"),
            models.CheckConstraint(condition=Q(monitoring_gap_seconds__gte=0), name="status_gap_nonnegative"),
            models.CheckConstraint(condition=(Q(state="RUNNING", valid=True) | (~Q(state="RUNNING") & Q(valid=False))), name="status_validity_consistent"),
        ]
