import math
from rest_framework import serializers
from common.serializers import SessionRecordSerializer
from .models import TelemetrySample, TrafficWindow
from detection.contract import eligible


class TelemetrySampleSerializer(SessionRecordSerializer):
    measurement_source = serializers.ChoiceField(choices=["OS_COUNTERS"], default="OS_COUNTERS")
    reason = serializers.CharField(max_length=255, allow_null=True, default=None)
    elapsed_seconds = serializers.FloatField(min_value=0)
    upload_bytes_per_second = serializers.FloatField(min_value=0, allow_null=True)
    download_bytes_per_second = serializers.FloatField(min_value=0, allow_null=True)

    class Meta:
        model = TelemetrySample
        fields = SessionRecordSerializer.identity_fields + (
            "observed_at", "elapsed_seconds", "measurement_source", "valid", "reason",
            "bytes_sent", "bytes_received", "packets_sent", "packets_received",
            "delta_bytes_sent", "delta_bytes_received", "delta_packets_sent", "delta_packets_received",
            "upload_bytes_per_second", "download_bytes_per_second")
        extra_kwargs = {f"delta_{name}": {"required": True} for name in (
            "bytes_sent", "bytes_received", "packets_sent", "packets_received")}
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        elapsed = attrs["elapsed_seconds"]
        if elapsed <= 0:
            raise serializers.ValidationError({"elapsed_seconds": "Must be positive."})
        rates = (attrs["upload_bytes_per_second"], attrs["download_bytes_per_second"])
        names = ("bytes_sent", "bytes_received", "packets_sent", "packets_received")
        deltas = [attrs["delta_" + name] for name in names]
        if attrs["valid"]:
            if attrs["reason"] is not None or elapsed > 3 or any(v is None for v in (*rates, *deltas)):
                raise serializers.ValidationError("Valid samples require rates/deltas, no reason, and an interval <=3 seconds.")
            for name, delta in zip(names, deltas):
                if delta > attrs[name]:
                    raise serializers.ValidationError({"delta_" + name: "Cannot exceed the cumulative counter."})
            for rate, delta in zip(rates, deltas):
                if not math.isclose(rate, delta / elapsed, rel_tol=1e-6, abs_tol=1e-6):
                    raise serializers.ValidationError("Rates must equal byte deltas / measured elapsed seconds.")
        elif not attrs["reason"] or any(v is not None for v in (*rates, *deltas)):
            raise serializers.ValidationError("Invalid samples require a reason and null rates/deltas.")
        return attrs


class TrafficWindowSerializer(SessionRecordSerializer):
    measurement_source = serializers.ChoiceField(choices=["PACKET_METADATA"], default="PACKET_METADATA")
    schema_version = serializers.ChoiceField(choices=["backend-window-v1"], default="backend-window-v1")
    kernel_loss = serializers.ChoiceField(choices=["unknown"], default="unknown")
    reason = serializers.CharField(max_length=255, allow_null=True, default=None)

    class Meta:
        model = TrafficWindow
        fields = SessionRecordSerializer.identity_fields + (
            "start", "end", "finalized_at", "processed_at", "measurement_source", "schema_version",
            "partial", "valid", "reason", "packets", "ip_bytes", "outbound_packets", "inbound_packets",
            "unknown_packets", "outbound_bytes", "inbound_bytes", "unknown_bytes", "tcp_packets",
            "udp_packets", "other_packets", "flow_count", "dropped", "kernel_loss",
            "features", "feature_schema_version", "capture_context")
        extra_kwargs = {name: {"default": 0} for name in ("unknown_packets", "unknown_bytes", "other_packets", "dropped")}
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start, end = attrs["start"], attrs["end"]
        if (end - start).total_seconds() != 10 or start.microsecond or start.second % 10:
            raise serializers.ValidationError("Windows must be epoch-aligned, half-open ten-second intervals.")
        if attrs["finalized_at"] < start or attrs["processed_at"] < attrs["finalized_at"]:
            raise serializers.ValidationError("Invalid finalization/processing timestamps.")
        for total, components in (
            ("packets", ("outbound_packets", "inbound_packets", "unknown_packets")),
            ("packets", ("tcp_packets", "udp_packets", "other_packets")),
            ("ip_bytes", ("outbound_bytes", "inbound_bytes", "unknown_bytes")),
        ):
            if attrs[total] != sum(attrs[x] for x in components):
                raise serializers.ValidationError({total: "Component counts must sum exactly to the total."})
        if attrs["flow_count"] > min(10000, attrs["packets"]):
            raise serializers.ValidationError({"flow_count": "Exceeds observed packets or sensor flow cap."})
        if attrs["packets"] == 0 and attrs["ip_bytes"] != 0:
            raise serializers.ValidationError("An empty window cannot contain IP bytes.")
        for packet_count, byte_count in (("outbound_packets", "outbound_bytes"),
                                         ("inbound_packets", "inbound_bytes"),
                                         ("unknown_packets", "unknown_bytes")):
            if (attrs[packet_count] == 0) != (attrs[byte_count] == 0):
                raise serializers.ValidationError("Each direction must have both packets and IP bytes, or neither.")
        if attrs["partial"]:
            if attrs["valid"] or not attrs["reason"]:
                raise serializers.ValidationError("Partial windows must be invalid with an explicit reason.")
        elif (not attrs["valid"] or attrs["reason"] is not None or attrs["dropped"]
              or attrs["unknown_packets"] or attrs["other_packets"]
              or start < attrs["session"].started_at
              or (attrs["finalized_at"] - end).total_seconds() < 2):
            raise serializers.ValidationError("Complete windows require full session coverage, no drops/reason, and finalization at end+2 or later.")
        sidecar = ("features", "feature_schema_version", "capture_context")
        if any(attrs.get(key) is not None for key in sidecar):
            try:
                eligible(attrs)
            except (ValueError, KeyError, TypeError) as exc:
                raise serializers.ValidationError({"features": str(exc)}) from exc
        return attrs
