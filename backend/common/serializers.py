import math
from datetime import datetime
from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware
from rest_framework import serializers
from monitoring.models import MonitoringSession, Mode


class AwareDateTimeField(serializers.DateTimeField):
    def to_internal_value(self, value):
        try:
            parsed = value if isinstance(value, datetime) else parse_datetime(value)
        except (TypeError, ValueError):
            parsed = None
        if parsed is None or not is_aware(parsed):
            raise serializers.ValidationError("Use an ISO-8601 timestamp with Z or a UTC offset.")
        return super().to_internal_value(value)


class StrictModelSerializer(serializers.ModelSerializer):
    """Reject unrecognised fields instead of silently accepting payload blobs."""
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.DateTimeField: AwareDateTimeField,
    }
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected a JSON object.")
        allowed = {name for name, field in self.fields.items() if not field.read_only}
        unknown = set(data) - allowed
        if unknown:
            raise serializers.ValidationError({name: "Unknown or read-only field." for name in sorted(unknown)})
        for name, value in data.items():
            field = self.fields[name]
            if isinstance(field, serializers.BooleanField) and type(value) is not bool:
                raise serializers.ValidationError({name: "Expected a JSON boolean."})
            if isinstance(field, (serializers.FloatField, serializers.IntegerField)) and isinstance(value, bool):
                raise serializers.ValidationError({name: "A boolean is not a measurement."})
        result = super().to_internal_value(data)
        for name, value in result.items():
            if isinstance(value, float) and not math.isfinite(value):
                raise serializers.ValidationError({name: "Must be finite."})
        return result


class SessionRecordSerializer(StrictModelSerializer):
    id = serializers.UUIDField()
    session_id = serializers.PrimaryKeyRelatedField(
        source="session", queryset=MonitoringSession.objects.all(), pk_field=serializers.UUIDField())
    run_id = serializers.UUIDField(write_only=True)
    mode = serializers.ChoiceField(choices=Mode.choices, write_only=True)
    interface_name = serializers.CharField(max_length=255, write_only=True)
    received_at = serializers.DateTimeField(read_only=True)

    identity_fields = ("id", "session_id", "run_id", "mode", "interface_name", "received_at")

    def validate(self, attrs):
        session = attrs["session"]
        for field in ("run_id", "mode", "interface_name"):
            if attrs.pop(field) != getattr(session, field):
                raise serializers.ValidationError({field: "Must match the immutable monitoring session."})
        # Epoch-aligned partial startup windows can start before session startup.
        timestamp = attrs.get("observed_at", attrs.get("end"))
        if timestamp < session.started_at:
            raise serializers.ValidationError("Record predates this monitoring session.")
        return attrs

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result.update(run_id=str(instance.session.run_id), mode=instance.session.mode,
                      interface_name=instance.session.interface_name)
        return result
