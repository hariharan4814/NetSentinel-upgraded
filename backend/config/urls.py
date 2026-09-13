from django.urls import path
from monitoring.views import HealthView, MonitoringSessionView, CaptureStatusView
from telemetry.views import TelemetryView, TrafficWindowView

urlpatterns = [
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/monitoring-sessions/", MonitoringSessionView.as_view(), name="sessions"),
    path("api/v1/telemetry/", TelemetryView.as_view(), name="telemetry"),
    path("api/v1/windows/", TrafficWindowView.as_view(), name="windows"),
    path("api/v1/capture-status/", CaptureStatusView.as_view(), name="capture-status"),
]
