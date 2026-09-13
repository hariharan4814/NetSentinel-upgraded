"""Explicit, in-memory SQLite test settings; never selected by normal startup."""
import sys
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F403

if len(sys.argv) < 2 or sys.argv[1] not in {"test", "check", "makemigrations"}:
    raise ImproperlyConfigured("SQLite settings are restricted to test, check and makemigrations commands.")

SECRET_KEY = "test-only-not-a-runtime-secret-" * 3
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
