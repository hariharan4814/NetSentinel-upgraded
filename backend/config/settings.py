"""PostgreSQL only at runtime. Environment variables override the root .env."""
import os
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from .base import *  # noqa: F403

load_dotenv(BASE_DIR.parent / ".env", override=False, interpolate=False)


def required(name):
    value = os.environ.get(name, "")
    if not value or value.startswith("replace-with-"):
        raise ImproperlyConfigured(f"Set {name} in the environment or repository .env")
    return value


SECRET_KEY = required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must contain at least 50 characters")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
NETSENTINEL_READ_TOKEN = os.environ.get("NETSENTINEL_READ_TOKEN", "")
NETSENTINEL_INGEST_TOKEN = os.environ.get("NETSENTINEL_INGEST_TOKEN", "")
NETSENTINEL_MODEL_TOKEN = os.environ.get("NETSENTINEL_MODEL_TOKEN", "")
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": required("POSTGRES_DB"),
    "USER": required("POSTGRES_USER"),
    "PASSWORD": required("POSTGRES_PASSWORD"),
    "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "CONN_MAX_AGE": 0,
    "OPTIONS": {"connect_timeout": 5, "sslmode": os.environ.get("POSTGRES_SSLMODE", "prefer")},
}}
