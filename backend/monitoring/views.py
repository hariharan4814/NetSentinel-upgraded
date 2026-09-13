from django.db import connection, DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from common.api import create_record
from common.reads import SessionQuery, RecentRecordsMixin
from .models import MonitoringSession
from .serializers import MonitoringSessionSerializer, CaptureStatusSerializer


class HealthView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            return Response({"status": "unavailable", "database": "unavailable"}, status=503)
        return Response({"status": "ok", "database": "reachable"})


class IngestView(APIView):
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return create_record(serializer)


class MonitoringSessionView(IngestView):
    serializer_class = MonitoringSessionSerializer

    def get(self, request):
        query = SessionQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        session = MonitoringSession.objects.filter(**query.validated_data).first()
        if session is None:
            raise NotFound("Session not found for the requested mode.")
        return Response(self.serializer_class(session).data)


class CaptureStatusView(RecentRecordsMixin, IngestView):
    serializer_class = CaptureStatusSerializer
    time_field = "observed_at"
