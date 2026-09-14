"""Metadata only. Django never loads or executes a model artifact."""
from django.db import models
from monitoring.models import SessionRecord


class ModelVersion(models.Model):
    id = models.UUIDField(primary_key=True)
    manifest = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    payload_digest = models.CharField(max_length=64, editable=False)


class AnomalyResult(SessionRecord):
    window = models.ForeignKey("telemetry.TrafficWindow", on_delete=models.CASCADE)
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT)
    observed_at = models.DateTimeField()
    scored_at = models.DateTimeField()
    anomaly_score = models.FloatField()
    label = models.CharField(max_length=10, choices=[("NORMAL", "NORMAL"), ("ANOMALOUS", "ANOMALOUS")])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["window", "model_version"], name="score_window_model_unique"),
            models.CheckConstraint(condition=models.Q(label__in=["NORMAL", "ANOMALOUS"]), name="score_label_valid"),
            models.CheckConstraint(condition=models.Q(anomaly_score__gte=0, anomaly_score__lte=1), name="score_bounds"),
        ]
        indexes = [models.Index(fields=["session", "observed_at"], name="score_session_observed_idx")]
