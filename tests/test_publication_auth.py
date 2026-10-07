"""Offline publication-transport fixtures; no capture, HTTP server or secrets."""
import os
import unittest
from unittest.mock import MagicMock, patch
from ml.__main__ import publish


class PublicationAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.record = {"session": {"mode": "SIMULATION", "session_id": "fixture"}, "window": {"valid": False}}
        self.dataset = {"rows": [self.record]}
        self.tokens = {"NETSENTINEL_INGEST_TOKEN": "fixture-ingest-not-for-runtime-0002",
                       "NETSENTINEL_MODEL_TOKEN": "fixture-model-not-for-runtime-00003"}

    def test_missing_credential_fails_before_network(self):
        with patch.dict(os.environ, {}, clear=True), patch("ml.__main__.rows", return_value=[self.record]), patch("ml.__main__.build_opener") as opener:
            with self.assertRaisesRegex(ValueError, "NETSENTINEL_INGEST_TOKEN"):
                publish(self.dataset, "http://127.0.0.1:8001")
            opener.assert_not_called()

    def test_publication_uses_route_scoped_keys_and_stops_after_bounded_requests(self):
        opener = MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.status = 201
        response.read.return_value = b"{}"
        manifest = {"id": "model-fixture"}
        scores = {"dataset_sha256": "fixture-digest", "model_version_id": "model-fixture", "results": [{"mode": "SIMULATION"}]}
        with patch.dict(os.environ, self.tokens, clear=True), patch("ml.__main__.rows", return_value=[self.record]), patch("ml.__main__.validate_manifest"), patch("ml.__main__.digest", return_value="fixture-digest"), patch("ml.__main__.build_opener", return_value=opener):
            self.assertEqual(publish(self.dataset, "http://127.0.0.1:8001", manifest, scores)["successful_requests"], 4)
        for i, call in enumerate(opener.open.call_args_list):
            request = call.args[0]
            self.assertEqual(request.get_header("Authorization"), "Bearer " + self.tokens["NETSENTINEL_INGEST_TOKEN" if i < 2 else "NETSENTINEL_MODEL_TOKEN"])
            self.assertEqual(call.kwargs["timeout"], 5)

    def test_reused_credentials_and_remote_hosts_fail_before_network(self):
        with patch.dict(os.environ, self.tokens | {"NETSENTINEL_MODEL_TOKEN": self.tokens["NETSENTINEL_INGEST_TOKEN"]}, clear=True), patch("ml.__main__.rows", return_value=[self.record]), patch("ml.__main__.build_opener") as opener:
            with self.assertRaisesRegex(ValueError, "separate credentials"):
                publish(self.dataset, "http://127.0.0.1:8001", {}, {})
            with self.assertRaisesRegex(ValueError, "loopback"):
                publish(self.dataset, "https://external.example")
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
