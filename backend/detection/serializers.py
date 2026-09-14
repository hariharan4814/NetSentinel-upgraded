from rest_framework import serializers
from common.serializers import StrictModelSerializer, SessionRecordSerializer
from telemetry.models import TrafficWindow
from telemetry.serializers import TrafficWindowSerializer
from .contract import validate_manifest, eligible, profile, aware
from .models import ModelVersion, AnomalyResult


class ModelVersionSerializer(StrictModelSerializer):
    id = serializers.UUIDField()

    class Meta:
        model = ModelVersion
        fields = ("id", "manifest", "received_at")
        read_only_fields = ("received_at",)
        validators = []

    def validate(self, attrs):
        try:
            manifest = validate_manifest(attrs["manifest"])
            if str(attrs["id"]) != manifest["id"]:
                raise ValueError("Model ID must match immutable manifest")
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise serializers.ValidationError({"manifest": str(exc)}) from exc
        return attrs


class AnomalyResultSerializer(SessionRecordSerializer):
    window_id = serializers.PrimaryKeyRelatedField(source="window", queryset=TrafficWindow.objects.select_related("session"), pk_field=serializers.UUIDField())
    model_version_id = serializers.PrimaryKeyRelatedField(source="model_version", queryset=ModelVersion.objects.all(), pk_field=serializers.UUIDField())

    class Meta:
        model = AnomalyResult
        fields = SessionRecordSerializer.identity_fields + ("window_id", "model_version_id", "observed_at", "scored_at", "anomaly_score", "label")
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        window, session = attrs["window"], attrs["session"]
        try:
            if window.session_id != session.pk or attrs["observed_at"] != window.end or attrs["scored_at"] < window.finalized_at:
                raise ValueError("Score window/session/timestamp mismatch")
            w = dict(TrafficWindowSerializer(window).data)
            eligible(w)
            s = {key: str(getattr(session, key)) for key in ("session_id", "run_id", "source_id", "interface_name", "mode", "observation_profile", "started_at")}
            manifest = validate_manifest(attrs["model_version"].manifest)
            if attrs["scored_at"] < aware(manifest["trained_at"]):
                raise ValueError("Score predates model training")
            if profile(s, w) != manifest["profile"]:
                raise ValueError("Model provenance/profile mismatch")
            value = attrs["anomaly_score"]
            if not 0 <= value <= 1 or attrs["label"] != ("ANOMALOUS" if value > manifest["threshold"] else "NORMAL"):
                raise ValueError("Score/label must match model threshold")
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return attrs
