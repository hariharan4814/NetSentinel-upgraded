from django.db import models
from django.db.models import Q, F
from monitoring.models import SessionRecord


class TelemetrySample(SessionRecord):
    observed_at = models.DateTimeField()
    elapsed_seconds = models.FloatField()
    measurement_source = models.CharField(max_length=20, default="OS_COUNTERS")
    valid = models.BooleanField()
    reason = models.CharField(max_length=255, null=True, blank=True)
    bytes_sent = models.PositiveBigIntegerField()
    bytes_received = models.PositiveBigIntegerField()
    packets_sent = models.PositiveBigIntegerField()
    packets_received = models.PositiveBigIntegerField()
    delta_bytes_sent = models.PositiveBigIntegerField(null=True, blank=True)
    delta_bytes_received = models.PositiveBigIntegerField(null=True, blank=True)
    delta_packets_sent = models.PositiveBigIntegerField(null=True, blank=True)
    delta_packets_received = models.PositiveBigIntegerField(null=True, blank=True)
    upload_bytes_per_second = models.FloatField(null=True, blank=True)
    download_bytes_per_second = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "observed_at"], name="sample_session_observed_unique"),
            models.CheckConstraint(condition=Q(elapsed_seconds__gt=0), name="sample_elapsed_positive"),
            models.CheckConstraint(condition=(Q(valid=True, upload_bytes_per_second__gte=0, download_bytes_per_second__gte=0, upload_bytes_per_second__isnull=False, download_bytes_per_second__isnull=False, reason__isnull=True) | Q(valid=False, upload_bytes_per_second__isnull=True, download_bytes_per_second__isnull=True, reason__isnull=False)), name="sample_validity_consistent"),
        ]


class TrafficWindow(SessionRecord):
    # Optional additive host-v1 sidecar. Legacy records remain unscorable.
    features = models.JSONField(null=True, blank=True)
    feature_schema_version = models.CharField(max_length=40, null=True, blank=True)
    capture_context = models.JSONField(null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    finalized_at = models.DateTimeField()
    processed_at = models.DateTimeField()
    measurement_source = models.CharField(max_length=20, default="PACKET_METADATA")
    schema_version = models.CharField(max_length=40, default="backend-window-v1")
    partial = models.BooleanField()
    valid = models.BooleanField()
    reason = models.CharField(max_length=255, null=True, blank=True)
    packets = models.PositiveBigIntegerField()
    ip_bytes = models.PositiveBigIntegerField()
    outbound_packets = models.PositiveBigIntegerField()
    inbound_packets = models.PositiveBigIntegerField()
    unknown_packets = models.PositiveBigIntegerField(default=0)
    outbound_bytes = models.PositiveBigIntegerField()
    inbound_bytes = models.PositiveBigIntegerField()
    unknown_bytes = models.PositiveBigIntegerField(default=0)
    tcp_packets = models.PositiveBigIntegerField()
    udp_packets = models.PositiveBigIntegerField()
    other_packets = models.PositiveBigIntegerField(default=0)
    flow_count = models.PositiveIntegerField()
    dropped = models.PositiveIntegerField(default=0)
    kernel_loss = models.CharField(max_length=10, default="unknown")

    class Meta:
        indexes = [models.Index(fields=["session", "end"], name="window_session_end_idx")]
        constraints = [
            models.UniqueConstraint(fields=["session", "start"], name="window_session_start_unique"),
            models.CheckConstraint(condition=Q(end__gt=F("start")), name="window_time_order"),
            models.CheckConstraint(condition=Q(packets=F("outbound_packets") + F("inbound_packets") + F("unknown_packets")), name="window_packet_conservation"),
            models.CheckConstraint(condition=Q(ip_bytes=F("outbound_bytes") + F("inbound_bytes") + F("unknown_bytes")), name="window_byte_conservation"),
            models.CheckConstraint(condition=Q(packets=F("tcp_packets") + F("udp_packets") + F("other_packets")), name="window_protocol_conservation"),
            models.CheckConstraint(condition=(Q(partial=False, valid=True, reason__isnull=True, dropped=0) | Q(partial=True, valid=False, reason__isnull=False)), name="window_validity_consistent"),
        ]
