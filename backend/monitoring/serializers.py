from rest_framework import serializers
from common.serializers import StrictModelSerializer, SessionRecordSerializer, AwareDateTimeField
from .models import MonitoringSession, CaptureStatus


class MonitoringSessionSerializer(StrictModelSerializer):
    session_id = serializers.UUIDField()
    schema_version = serializers.ChoiceField(choices=["backend-v1"], default="backend-v1")

    class Meta:
        model = MonitoringSession
        fields = ("session_id", "source_id", "run_id", "interface_name", "mode", "started_at",
                  "observation_profile", "schema_version", "received_at")
        read_only_fields = ("received_at",)
        validators = []


class CaptureStatusSerializer(SessionRecordSerializer):
    monitoring_gap_seconds = serializers.FloatField(min_value=0, default=0)
    reason = serializers.CharField(max_length=255, allow_null=True, default=None)
    loss_started_at = AwareDateTimeField(allow_null=True, default=None)
    gap_ended_at = AwareDateTimeField(allow_null=True, default=None)
    recovery_attempts = serializers.IntegerField(min_value=0, max_value=2**31-1, default=0)

    class Meta:
        model = CaptureStatus
        fields = SessionRecordSerializer.identity_fields + (
            "observed_at", "state", "valid", "reason", "loss_started_at",
            "gap_ended_at", "monitoring_gap_seconds", "recovery_attempts")
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["valid"] != (attrs["state"] == "RUNNING"):
            raise serializers.ValidationError({"valid": "Only RUNNING status is valid."})
        if not attrs["valid"] and not attrs["reason"]:
            raise serializers.ValidationError({"reason": "Required for non-running status."})
        loss, end, observed = attrs["loss_started_at"], attrs["gap_ended_at"], attrs["observed_at"]
        if loss and loss > observed or end and (not loss or not loss <= end <= observed):
            raise serializers.ValidationError("Invalid loss/recovery timestamp ordering.")
        return attrs
