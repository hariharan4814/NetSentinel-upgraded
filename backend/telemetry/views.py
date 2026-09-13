from common.reads import RecentRecordsMixin
from monitoring.views import IngestView
from .serializers import TelemetrySampleSerializer, TrafficWindowSerializer


class RecentRecordsView(RecentRecordsMixin, IngestView):
    pass


class TelemetryView(RecentRecordsView):
    serializer_class = TelemetrySampleSerializer
    time_field = "observed_at"


class TrafficWindowView(RecentRecordsView):
    serializer_class = TrafficWindowSerializer
    time_field = "end"
