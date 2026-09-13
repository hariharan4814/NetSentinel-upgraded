import hashlib
import json
from django.db import DatabaseError, IntegrityError, transaction, connection
from django.db.models import Model
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from monitoring.models import MonitoringSession


class Conflict(APIException):
    status_code = 409
    default_detail = "Record identity already exists with different content or a different record ID."
    default_code = "conflict"


def exception_handler(exc, context):
    if isinstance(exc, DatabaseError):
        return Response({"error": "database_unavailable"}, status=503)
    return drf_exception_handler(exc, context)


def create_record(serializer):
    """Unique keys plus atomic insertion make retries safe under concurrent POSTs."""
    attrs = serializer.validated_data
    normalized = {k: v.pk if isinstance(v, Model) else v for k, v in attrs.items()}
    # str(datetime) retains all six microsecond digits (DjangoJSONEncoder truncates).
    digest = hashlib.sha256(json.dumps(normalized, default=str, sort_keys=True,
                                      separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    model = serializer.Meta.model
    pk_name = model._meta.pk.name
    pk = attrs[pk_name]
    try:
        with transaction.atomic():
            if model is MonitoringSession:
                # Serialize even the first two registrations for a run on PostgreSQL.
                # SQLite is used only by single-writer automated tests.
                if connection.vendor == "postgresql":
                    lock_key = attrs["run_id"].int % (2**64) - 2**63
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])
                existing = model.objects.filter(run_id=attrs["run_id"]).first()
                if existing and any(getattr(existing, field) != attrs[field] for field in (
                    "source_id", "mode", "interface_name", "observation_profile"
                )):
                    raise Conflict("Run ID is already bound to a different source, mode, interface or observation profile.")
            instance, created = model.objects.get_or_create(
                pk=pk, defaults={**attrs, "payload_digest": digest})
            if instance.payload_digest != digest:
                raise Conflict()
    except IntegrityError:
        # A different ID reusing a natural key is a conflict, never a rewrite.
        raise Conflict() from None
    return Response(serializer.__class__(instance).data, status=201 if created else 200)
