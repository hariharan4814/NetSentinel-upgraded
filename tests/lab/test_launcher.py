"""Launcher credential isolation and fixed health probes; no service started."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.request

spec = importlib.util.spec_from_file_location("lab_launcher", Path(__file__).resolve().parents[2] / "scripts/run_ai_lab.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_children_do_not_inherit_unrelated_application_credentials(self):
        source = {"PATH": "fixture-path", "NetSentinel_MODEL_TOKEN": "fixture-secret",
                  "POSTGRES_PASSWORD": "fixture-db-secret", "DJANGO_SECRET_KEY": "fixture-key",
                  "DJANGO_SETTINGS_MODULE": "config.settings", "BACKEND_API_BASE_URL": "http://elsewhere.invalid"}
        stack = launcher.LabStack("a" * 64)
        with patch.dict(os.environ, source, clear=True):
            environment = stack.environment()
        self.assertEqual(environment, {"PATH": "fixture-path", "PYTHONUNBUFFERED": "1"})

    def test_health_probe_redirect_is_not_followed(self):
        request = urllib.request.Request("http://127.0.0.1:8811/api/v1/lab/jobs/",
                                         headers={"Authorization": "Bearer fixture-only"})
        self.assertIsNone(launcher.NoRedirect().redirect_request(request, None, 302, "Found", {}, "https://example.invalid"))

    def test_ports_and_password_are_validated_before_startup(self):
        for arguments in ({"backend_port": 3105, "frontend_port": 3105},
                          {"backend_port": 80}, {"frontend_port": True}):
            with self.assertRaises(ValueError):
                launcher.LabStack("a" * 64, **arguments)
        for password in ("short", "a" * 31 + " ", "replace-with-" + "a" * 50):
            with self.assertRaises(ValueError):
                launcher.LabStack(password)
