from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, DatabaseError):
        return Response({"error": "database_unavailable"}, status=503)
    return drf_exception_handler(exc, context)
