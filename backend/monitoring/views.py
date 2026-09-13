from django.db import connection, DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView
from common.api import create_record
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


class CaptureStatusView(IngestView):
    serializer_class = CaptureStatusSerializer
