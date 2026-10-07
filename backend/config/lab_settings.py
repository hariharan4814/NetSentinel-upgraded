"""Explicit standalone AI Lab runtime, never an automatic PostgreSQL fallback.

Only simulation jobs are installed. Existing telemetry, research data, models
and the normal config.settings PostgreSQL database are not accessible here.
"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from .base import *  # noqa: F403

load_dotenv(BASE_DIR.parent / ".env", override=False, interpolate=False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-with-"):
    raise ImproperlyConfigured("Configure DJANGO_SECRET_KEY before starting the explicit lab runtime.")
INSTALLED_APPS = ["rest_framework", "experiments"]
ROOT_URLCONF = "config.lab_urls"
database_path = Path(os.environ.get("NETSENTINEL_LAB_DATABASE_PATH", str(BASE_DIR.parent / "artifacts/lab/demo.sqlite3"))).resolve()
database_path.parent.mkdir(parents=True, exist_ok=True)
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(database_path),
                         "OPTIONS": {"timeout": 20}}}
NETSENTINEL_READ_TOKEN = os.environ.get("NETSENTINEL_READ_TOKEN", "")
NETSENTINEL_LAB_TOKEN = os.environ.get("NETSENTINEL_LAB_TOKEN", "")
NETSENTINEL_LAB_WORKER_TOKEN = os.environ.get("NETSENTINEL_LAB_WORKER_TOKEN", "")
# Ingest/model scopes intentionally remain disabled in this runtime.
REST_FRAMEWORK = {**REST_FRAMEWORK, "EXCEPTION_HANDLER": "experiments.errors.exception_handler"}
