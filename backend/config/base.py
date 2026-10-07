"""Shared API configuration; database and secret are supplied by settings."""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
# The lab's validation contract is standard-library-only and shared with its
# independent CLI. Do not import lab.pipeline (ML) in this web process.
sys.path.insert(0, str(BASE_DIR.parent))
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
INSTALLED_APPS = ["rest_framework", "monitoring", "telemetry", "detection", "experiments"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "common.middleware.LocalOnlyMiddleware"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
# Runtime values are loaded after .env in settings.py. Empty values fail closed.
NETSENTINEL_READ_TOKEN = ""
NETSENTINEL_INGEST_TOKEN = ""
NETSENTINEL_MODEL_TOKEN = ""
NETSENTINEL_LAB_TOKEN = ""
NETSENTINEL_LAB_WORKER_TOKEN = ""
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "common.api.exception_handler",
    "STRICT_JSON": True,
}
