from django.urls import path
from monitoring.views import HealthView, MonitoringSessionView, CaptureStatusView
from telemetry.views import TelemetryView, TrafficWindowView
from detection.views import ModelVersionView, AnomalyResultView

urlpatterns = [
    path("api/v1/model-versions/", ModelVersionView.as_view(), name="model-versions"),
    path("api/v1/anomaly-results/", AnomalyResultView.as_view(), name="anomaly-results"),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/monitoring-sessions/", MonitoringSessionView.as_view(), name="sessions"),
    path("api/v1/telemetry/", TelemetryView.as_view(), name="telemetry"),
    path("api/v1/windows/", TrafficWindowView.as_view(), name="windows"),
    path("api/v1/capture-status/", CaptureStatusView.as_view(), name="capture-status"),
]
