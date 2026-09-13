from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from monitoring.models import Mode
from monitoring.views import IngestView
from .serializers import TelemetrySampleSerializer, TrafficWindowSerializer


class RecentQuery(serializers.Serializer):
    session_id = serializers.UUIDField()
    mode = serializers.ChoiceField(choices=Mode.choices)
    limit = serializers.IntegerField(min_value=1, max_value=200, default=50)
    cursor = serializers.CharField(required=False)


class RecentPagination(CursorPagination):
    page_size_query_param = "limit"
    max_page_size = 200
    page_size = 50


class RecentRecordsView(IngestView):
    def get(self, request):
        query = RecentQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        # Observation time defines recent traffic; receipt time cannot revive old replay.
        now = timezone.now()
        records = self.serializer_class.Meta.model.objects.select_related("session").filter(
            session_id=params["session_id"], session__mode=params["mode"],
            **{self.time_field + "__gte": now - timedelta(hours=24), self.time_field + "__lte": now})
        paginator = RecentPagination()
        paginator.ordering = ("-" + self.time_field, "-id")
        page = paginator.paginate_queryset(records, request, view=self)
        return paginator.get_paginated_response(self.serializer_class(page, many=True).data)


class TelemetryView(RecentRecordsView):
    serializer_class = TelemetrySampleSerializer
    time_field = "observed_at"


class TrafficWindowView(RecentRecordsView):
    serializer_class = TrafficWindowSerializer
    time_field = "end"
