"""Explicit, in-memory SQLite test settings; never selected by normal startup."""
import sys
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F403

if len(sys.argv) < 2 or sys.argv[1] not in {"test", "check", "makemigrations"}:
    raise ImproperlyConfigured("SQLite settings are restricted to test, check and makemigrations commands.")

SECRET_KEY = "test-only-not-a-runtime-secret-" * 3
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
# Deliberately public synthetic fixture values; never valid runtime credentials.
NETSENTINEL_READ_TOKEN = "fixture-read-only-not-for-runtime-0001"
NETSENTINEL_INGEST_TOKEN = "fixture-ingest-not-for-runtime-0002"
NETSENTINEL_MODEL_TOKEN = "fixture-model-not-for-runtime-00003"
