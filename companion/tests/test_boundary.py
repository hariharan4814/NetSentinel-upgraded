"""Offline HTTP parser/authorization fixtures; never starts an elevated broker."""
from email.message import Message
import io
import unittest
from companion.http_boundary import APIError, Handler, authorize

KEY = "fixture-local-key-not-valid-for-runtime-1234"


class BoundaryTests(unittest.TestCase):
    def call(self, **changes):
        values = dict(peer="127.0.0.1", hosts=["127.0.0.1:8765"], origin=None,
                      port=8765, authorization="Bearer " + KEY, secret=KEY)
        values.update(changes)
        return authorize(**values)

    def rejects(self, status, **changes):
        with self.assertRaises(APIError) as error:
            self.call(**changes)
        self.assertEqual(error.exception.status, status)

    def test_loopback_peer_exact_single_host_and_no_equivalent_origin_alias(self):
        self.call()
        for hosts in ([], ["localhost:8765"], ["127.0.0.1:8765", "127.0.0.1:8765"],
                      ["external.example:8765"], ["127.0.0.1:9999"], ["127.0.0.1:8765,external.example"]):
            self.rejects(403, hosts=hosts)
        for peer in ("192.0.2.4", "invalid", ""):
            self.rejects(403, peer=peer)
        for origin in ("http://localhost:8765", "null", "https://external.example", "http://127.0.0.1:8766"):
            self.rejects(403, origin=origin)

    def test_mutations_require_exact_origin_and_broker_forbids_any_origin(self):
        self.rejects(403, method="POST")
        self.call(method="POST", origin="http://127.0.0.1:8765")
        self.call(method="POST", broker=True)
        self.rejects(403, broker=True, origin="http://127.0.0.1:8765")
        self.rejects(403, broker=True, origin="")

    def test_credential_validation_is_separate_from_transport(self):
        for authorization in (None, "", "Bearer wrong", "Bearer " + "x" * 301, KEY):
            self.rejects(401, authorization=authorization)
        self.rejects(401, secret="short", authorization="Bearer short")

    def parse(self, body, headers):
        handler = object.__new__(Handler)
        handler.rfile = io.BytesIO(body)
        handler.headers = Message()
        for name, value in headers:
            handler.headers[name] = value
        return handler.body()

    def test_body_is_bounded_json_object_and_rejects_ambiguous_length(self):
        self.assertEqual(self.parse(b'{"consent":true}', [("Content-Length", "16"), ("Content-Type", "application/json")]), {"consent": True})
        for headers in ([('Content-Type', 'application/json')],
                        [('Content-Length', '2'), ('Content-Length', '2'), ('Content-Type', 'application/json')],
                        [('Content-Length', '2'), ('Transfer-Encoding', 'chunked'), ('Content-Type', 'application/json')],
                        [('Content-Length', '999999'), ('Content-Type', 'application/json')],
                        [('Content-Length', '2'), ('Content-Type', 'text/plain')]):
            with self.assertRaises(APIError):
                self.parse(b'{}', headers)
        for body in (b'[]', b'null', b'{bad}', b'\xff\xff'):
            with self.assertRaises(APIError):
                self.parse(body, [("Content-Length", str(len(body))), ("Content-Type", "application/json")])


if __name__ == "__main__":
    unittest.main()
