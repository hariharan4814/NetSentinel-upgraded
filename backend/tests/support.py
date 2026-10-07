"""Authenticate synthetic regression fixtures using the route's proper scope."""
from django.conf import settings
from rest_framework.test import APIClient


class ScopedFixtureClient(APIClient):
    def generic(self, method, path, *args, **kwargs):
        token = settings.NETSENTINEL_READ_TOKEN
        if method == "POST":
            token = (settings.NETSENTINEL_MODEL_TOKEN if path in (
                "/api/v1/model-versions/", "/api/v1/anomaly-results/")
                else settings.NETSENTINEL_INGEST_TOKEN)
        kwargs.setdefault("HTTP_AUTHORIZATION", f"Bearer {token}")
        return super().generic(method, path, *args, **kwargs)
