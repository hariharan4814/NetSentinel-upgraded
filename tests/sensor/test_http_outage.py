"""Offline failure containment tests; live HTTP refusal is explicitly opt-in."""
from copy import deepcopy
import http.client
import unittest
from unittest.mock import Mock, patch

from http_outage import OutageMirror


class HttpOutageTests(unittest.TestCase):
    def record(self):
        return {"type": "health", "mode": "LIVE", "session_id": "fixture",
                "normalized": 7, "totals": {"bytes_sent": 123}}

    def test_refusal_timeout_and_http_failure_preserve_local_records_without_retries(self):
        for error in (ConnectionRefusedError(), TimeoutError(), http.client.HTTPException()):
            with self.subTest(error=type(error).__name__):
                local, record = [], self.record()
                original = deepcopy(record)
                with patch("http_outage.http.client.HTTPConnection") as factory:
                    connection = factory.return_value
                    def request(*args):
                        self.assertIs(local[0], record)  # Local output precedes HTTP.
                        raise error
                    connection.request.side_effect = request
                    sink = OutageMirror(local.append, 12345)
                    for _ in range(100):
                        sink(record)
                    sink({"type": "capture_stopped"})
                    factory.assert_called_once_with("127.0.0.1", 12345, timeout=.2)
                    connection.close.assert_called_once()
                self.assertEqual(record, original)
                self.assertEqual(len([r for r in local if r["type"] == "health"]), 100)
                self.assertEqual(local[-1]["type"], "capture_stopped")
                self.assertEqual(sink.discarded, 100)
                self.assertEqual(sink.accepted, 0)
                self.assertEqual(sink.summary()["queued"], 0)
                self.assertEqual(len([r for r in local if r["type"] == "http_outage"]), 1)

    def test_http_503_is_failure_not_delivery(self):
        with patch("http_outage.http.client.HTTPConnection") as factory:
            factory.return_value.getresponse.return_value.status = 503
            sink = OutageMirror(Mock(), 12345)
            sink(self.record())
        self.assertEqual(sink.failure, "HTTPException")
        self.assertEqual((sink.accepted, sink.discarded), (0, 1))

    def test_unexpected_success_is_not_reported_as_outage(self):
        with patch("http_outage.http.client.HTTPConnection") as factory:
            factory.return_value.getresponse.return_value.status = 204
            sink = OutageMirror(Mock(), 12345)
            sink(self.record())
        self.assertIsNone(sink.failure)
        self.assertEqual((sink.accepted, sink.discarded), (1, 0))

    def test_local_output_failure_is_not_swallowed(self):
        with patch("http_outage.http.client.HTTPConnection") as factory:
            with self.assertRaises(BrokenPipeError):
                OutageMirror(Mock(side_effect=BrokenPipeError), 12345)(self.record())
            factory.assert_not_called()
