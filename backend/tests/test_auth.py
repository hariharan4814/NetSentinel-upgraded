"""Authentication boundaries only; synthetic credentials, no actual secrets."""
from django.conf import settings
from django.test import SimpleTestCase, override_settings, RequestFactory
from django.http import JsonResponse
from common.middleware import LocalOnlyMiddleware


class LocalAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = LocalOnlyMiddleware(lambda _: JsonResponse({"accepted": True}))

    def call(self, method="GET", path="/api/v1/health/", token=None, **headers):
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        request = self.factory.generic(method, path, "{}", content_type="application/json",
                                       HTTP_HOST="localhost", REMOTE_ADDR="127.0.0.1", **headers)
        return self.middleware(request)

    def test_missing_wrong_oversized_and_cookie_credentials_are_rejected(self):
        for token in (None, "wrong", "x" * 1000):
            response = self.call(token=token, HTTP_COOKIE="operator=pretend")
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response["Cache-Control"], "no-store")

    def test_read_key_is_read_only_and_ingestion_key_cannot_read_or_publish_models(self):
        self.assertEqual(self.call(token=settings.NETSENTINEL_READ_TOKEN).status_code, 200)
        self.assertEqual(self.call("POST", "/api/v1/windows/", settings.NETSENTINEL_READ_TOKEN).status_code, 403)
        for path in ("monitoring-sessions", "telemetry", "windows", "capture-status"):
            self.assertEqual(self.call("POST", f"/api/v1/{path}/", settings.NETSENTINEL_INGEST_TOKEN).status_code, 200)
        self.assertEqual(self.call(token=settings.NETSENTINEL_INGEST_TOKEN).status_code, 403)
        self.assertEqual(self.call("POST", "/api/v1/model-versions/", settings.NETSENTINEL_INGEST_TOKEN).status_code, 403)

    def test_model_key_only_publishes_model_metadata_and_results(self):
        for path in ("model-versions", "anomaly-results"):
            self.assertEqual(self.call("POST", f"/api/v1/{path}/", settings.NETSENTINEL_MODEL_TOKEN).status_code, 200)
        self.assertEqual(self.call("POST", "/api/v1/windows/", settings.NETSENTINEL_MODEL_TOKEN).status_code, 403)
        self.assertEqual(self.call(token=settings.NETSENTINEL_MODEL_TOKEN).status_code, 403)

    def test_missing_short_placeholder_and_duplicate_config_fail_closed(self):
        for value in ("", "short", "replace-with-a-long-enough-placeholder"):
            with override_settings(NETSENTINEL_READ_TOKEN=value):
                self.assertEqual(self.call(token=value).status_code, 401)
        with override_settings(NETSENTINEL_READ_TOKEN=settings.NETSENTINEL_INGEST_TOKEN):
            self.assertEqual(self.call(token=settings.NETSENTINEL_INGEST_TOKEN).status_code, 401)

    def test_browser_origins_even_empty_and_proxy_claims_cannot_authorize(self):
        for origin in ("", "http://localhost", "https://hostile.example"):
            self.assertEqual(self.call(token=settings.NETSENTINEL_READ_TOKEN, HTTP_ORIGIN=origin).status_code, 403)
        for value in ("cross-site", "same-site"):
            self.assertEqual(self.call(token=settings.NETSENTINEL_READ_TOKEN, HTTP_SEC_FETCH_SITE=value).status_code, 403)
        self.assertEqual(self.call(HTTP_X_FORWARDED_FOR="127.0.0.1", HTTP_X_FORWARDED_HOST="localhost").status_code, 401)

    def test_untrusted_forwarded_protocol_does_not_change_transport(self):
        self.assertEqual(self.call(token=settings.NETSENTINEL_READ_TOKEN, HTTP_X_FORWARDED_PROTO="https").status_code, 200)
