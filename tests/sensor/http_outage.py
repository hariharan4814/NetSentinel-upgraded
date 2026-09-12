"""Opt-in Sprint 1 HTTP failure fixture, not a production upload protocol.

Mirror one actual health record to a reserved, non-listening loopback endpoint.
Local delivery comes first. No retries, retained queue, or remote destinations.
"""
from contextlib import contextmanager
import http.client
import json
import socket


@contextmanager
def unavailable_endpoint():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as endpoint:
        endpoint.bind(("127.0.0.1", 0))
        # Keep the port reserved without listening for the entire experiment.
        yield endpoint.getsockname()[1]


class OutageMirror:
    def __init__(self, local_emit, port):
        self.local_emit = local_emit
        self.port = port
        self.attempts = self.accepted = self.discarded = 0
        self.failure = None

    def __call__(self, record):
        self.local_emit(record)
        if record["type"] != "health":
            return
        if self.attempts:
            self.discarded += 1
            return
        body = json.dumps(record, allow_nan=False).encode("utf-8")
        self.attempts += 1
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=.2)
        try:
            connection.request("POST", "/sprint1-outage-fixture", body,
                               {"Content-Type": "application/json"})
            response = connection.getresponse()
            if not 200 <= response.status < 300:
                raise http.client.HTTPException(f"HTTP status {response.status}")
            self.accepted += 1
        except (OSError, http.client.HTTPException) as exc:
            self.failure = type(exc).__name__
            self.discarded += 1
            self.local_emit({"type": "http_outage", "exception_type": self.failure,
                             "attempts": self.attempts, "circuit_open": True,
                             "normalized_at_failure": record["normalized"],
                             "session_id": record["session_id"], "mode": record["mode"]})
        finally:
            connection.close()

    def summary(self):
        return {"attempts": self.attempts, "accepted": self.accepted,
                "discarded": self.discarded, "failure": self.failure,
                "queued": 0, "retry_policy": "none; one attempt per validator process"}
