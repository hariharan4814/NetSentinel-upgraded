"""Loopback transport and method/route-scoped machine authentication.

No browser cookies are accepted here. The local Next server authenticates its
operator separately and holds only the read credential. No trusted proxies.
"""
from ipaddress import ip_address
import hashlib
import hmac
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.conf import settings


class LocalOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.get_host()  # Enforce ALLOWED_HOSTS even without CommonMiddleware.
        try:
            local = ip_address(request.META.get("REMOTE_ADDR", "")).is_loopback
        except ValueError:
            local = False
        def reject(error, status):
            response = JsonResponse({"error": error}, status=status)
            response["Cache-Control"] = "no-store"
            return response

        if not local or request.is_secure() or request.headers.get("Origin") is not None or request.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
            return reject("local_clients_only", 403)

        configured = {
            "read": settings.NETSENTINEL_READ_TOKEN,
            "ingest": settings.NETSENTINEL_INGEST_TOKEN,
            "model": settings.NETSENTINEL_MODEL_TOKEN,
        }
        def valid(value):
            return isinstance(value, str) and 32 <= len(value) <= 256 and value.isascii() and not any(c.isspace() for c in value) and not value.startswith("replace-with-")

        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or len(header) > 263:
            return reject("authentication_required", 401)
        candidate = hashlib.sha256(header[7:].encode()).digest()
        scope = None
        for name, token in configured.items():
            # Reusing a key across privilege levels fails closed for that key.
            if valid(token) and list(configured.values()).count(token) == 1 and hmac.compare_digest(candidate, hashlib.sha256(token.encode()).digest()):
                scope = name
        if scope is None:
            return reject("invalid_or_unconfigured_credential", 401)
        ingestion_paths = {f"/api/v1/{name}/" for name in ("monitoring-sessions", "telemetry", "windows", "capture-status")}
        model_paths = {"/api/v1/model-versions/", "/api/v1/anomaly-results/"}
        permitted = ((scope == "read" and request.method == "GET")
                     or (scope == "ingest" and request.method == "POST" and request.path in ingestion_paths)
                     or (scope == "model" and request.method == "POST" and request.path in model_paths))
        if not permitted:
            return reject("credential_scope_forbidden", 403)
        try:
            if len(request.body) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                raise RequestDataTooBig
        except RequestDataTooBig:
            return reject("request_too_large", 413)
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        return response
