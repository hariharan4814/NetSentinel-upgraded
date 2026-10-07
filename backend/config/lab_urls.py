"""Simulation jobs only; no LIVE sensor/model or security controls."""
from django.urls import path
from experiments import views

urlpatterns = [
    path("api/v1/lab/jobs/", views.JobsView.as_view()),
    path("api/v1/lab/jobs/<uuid:job_id>/", views.JobView.as_view()),
    path("api/v1/lab/jobs/<uuid:job_id>/cancel/", views.CancelView.as_view()),
    path("api/v1/lab/worker/claim/", views.ClaimView.as_view()),
    path("api/v1/lab/worker/<uuid:job_id>/heartbeat/", views.HeartbeatView.as_view()),
    path("api/v1/lab/worker/<uuid:job_id>/finish/", views.FinishView.as_view()),
]
