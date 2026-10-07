from django.urls import path
from monitoring.views import HealthView, MonitoringSessionView, CaptureStatusView
from telemetry.views import TelemetryView, TrafficWindowView
from detection.views import ModelVersionView, AnomalyResultView
from experiments import views as lab_views

urlpatterns = [
    path("api/v1/lab/jobs/", lab_views.JobsView.as_view()),
    path("api/v1/lab/jobs/<uuid:job_id>/", lab_views.JobView.as_view()),
    path("api/v1/lab/jobs/<uuid:job_id>/cancel/", lab_views.CancelView.as_view()),
    path("api/v1/lab/worker/claim/", lab_views.ClaimView.as_view()),
    path("api/v1/lab/worker/<uuid:job_id>/heartbeat/", lab_views.HeartbeatView.as_view()),
    path("api/v1/lab/worker/<uuid:job_id>/finish/", lab_views.FinishView.as_view()),
    path("api/v1/model-versions/", ModelVersionView.as_view(), name="model-versions"),
    path("api/v1/anomaly-results/", AnomalyResultView.as_view(), name="anomaly-results"),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/monitoring-sessions/", MonitoringSessionView.as_view(), name="sessions"),
    path("api/v1/telemetry/", TelemetryView.as_view(), name="telemetry"),
    path("api/v1/windows/", TrafficWindowView.as_view(), name="windows"),
    path("api/v1/capture-status/", CaptureStatusView.as_view(), name="capture-status"),
]
