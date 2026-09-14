"""Runtime configuration inspection without a database or local secret file."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class ConfigurationTests(SimpleTestCase):
    def test_sqlite_settings_cannot_start_runtime_commands(self):
        manage = Path(__file__).resolve().parents[1] / "manage.py"
        for command in ("runserver", "shell", "migrate"):
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, str(manage), command,
                                         "--settings=config.test_settings"],
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("SQLite settings are restricted", result.stderr)

    def runtime_settings(self, **changes):
        values = {"DJANGO_SECRET_KEY": "test-configuration-only-" * 3,
                  "POSTGRES_DB": "fixture_db", "POSTGRES_USER": "fixture_user",
                  "POSTGRES_PASSWORD": "fixture-not-a-runtime-password"}
        values.update(changes)
        values = {key: value for key, value in values.items() if value is not None}
        path = Path(__file__).resolve().parents[1] / "config/settings.py"
        spec = importlib.util.spec_from_file_location("config.runtime_probe", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, values, clear=True), patch("dotenv.load_dotenv"):
            spec.loader.exec_module(module)
        return module

    def test_runtime_is_postgresql_and_debug_is_off(self):
        settings = self.runtime_settings()
        self.assertEqual(settings.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(settings.DATABASES["default"]["HOST"], "127.0.0.1")
        self.assertEqual(settings.DATABASES["default"]["NAME"], "fixture_db")
        self.assertFalse(settings.DEBUG)
        self.assertEqual(settings.INSTALLED_APPS, ["rest_framework", "monitoring", "telemetry", "detection"])

    def test_required_configuration_fails_without_secrets_or_database_values(self):
        for name in ("DJANGO_SECRET_KEY", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
            with self.subTest(name=name), self.assertRaisesMessage(ImproperlyConfigured, name):
                self.runtime_settings(**{name: None})
        for value in ("short", "replace-with-a-long-placeholder-that-must-not-be-used-as-a-real-secret"):
            with self.assertRaises(ImproperlyConfigured):
                self.runtime_settings(DJANGO_SECRET_KEY=value)
