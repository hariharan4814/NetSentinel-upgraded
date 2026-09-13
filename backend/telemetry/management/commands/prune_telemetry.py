"""Explicit bounded cleanup; no scheduler, background worker or payload spool."""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import CaptureStatus
from telemetry.models import TelemetrySample, TrafficWindow


class Command(BaseCommand):
    help = "Delete at most 1000 records per table received over 24 hours ago; session manifests remain."

    def handle(self, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        for model in (TelemetrySample, TrafficWindow, CaptureStatus):
            keys = list(model.objects.filter(received_at__lt=cutoff).order_by("received_at").values_list("pk", flat=True)[:1000])
            count, _ = model.objects.filter(pk__in=keys).delete()
            self.stdout.write(f"{model.__name__}: deleted {count}")
