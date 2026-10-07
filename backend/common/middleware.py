"""Loopback transport and method/route-scoped machine authentication.

No browser cookies are accepted here. The local Next server authenticates its
operator separately and holds read and lab-job credentials. No trusted proxies.
"""
from ipaddress import ip_address
import hashlib
import hmac
import re
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
            "lab": settings.NETSENTINEL_LAB_TOKEN,
            "lab_worker": settings.NETSENTINEL_LAB_WORKER_TOKEN,
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
        job_mutation = re.fullmatch(r"/api/v1/lab/jobs/(?:[0-9a-f-]{36}/cancel/)?", request.path)
        worker_mutation = re.fullmatch(r"/api/v1/lab/worker/(?:claim/|[0-9a-f-]{36}/(?:heartbeat|finish)/)", request.path)
        permitted = ((scope == "read" and request.method == "GET")
                     or (scope == "ingest" and request.method == "POST" and request.path in ingestion_paths)
                     or (scope == "model" and request.method == "POST" and request.path in model_paths)
                     or (scope == "lab" and request.method == "POST" and job_mutation)
                     or (scope == "lab_worker" and request.method == "POST" and worker_mutation))
        if not permitted:
            return reject("credential_scope_forbidden", 403)
        # Authenticate and scope-check BEFORE granting the one larger body cap.
        # Read the stream with a bounded read so the global Django limit stays
        # 64 KiB for existing routes and cannot be raced by another request.
        limit = (4 * 1024 * 1024 if scope == "lab_worker" and request.path.endswith("/finish/")
                 else settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
        try:
            length = request.META.get("CONTENT_LENGTH", "")
            if length and (not length.isdecimal() or int(length) > limit):
                raise RequestDataTooBig
            body = request.read(limit + 1)
            if len(body) > limit:
                raise RequestDataTooBig
            from io import BytesIO
            request._body = body
            request._stream = BytesIO(body)
        except RequestDataTooBig:
            return reject("request_too_large", 413)
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        return response
