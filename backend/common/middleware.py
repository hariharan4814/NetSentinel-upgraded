"""Temporary local-only boundary while authentication is explicitly deferred."""
from ipaddress import ip_address
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
        if not local or request.headers.get("Origin") or request.headers.get("Sec-Fetch-Site") == "cross-site":
            return JsonResponse({"error": "local_clients_only"}, status=403)
        try:
            if len(request.body) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                raise RequestDataTooBig
        except RequestDataTooBig:
            return JsonResponse({"error": "request_too_large"}, status=413)
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        return response
