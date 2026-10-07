"""Strict loopback boundary with bounded requests and no forwarded-header trust."""
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address


class APIError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def authorize(peer, hosts, origin, port, authorization, secret, method="GET", broker=False):
    try:
        local = ip_address(peer).is_loopback
    except ValueError:
        local = False
    expected = f"127.0.0.1:{port}"
    if not local or hosts != [expected]:
        raise APIError(403, "Loopback host required")
    if (broker and origin is not None) or (origin is not None and origin != "http://"+expected):
        raise APIError(403, "Origin rejected")
    if method == "POST" and not broker and origin != "http://"+expected:
        raise APIError(403, "Same-origin browser request required")
    if not secret or len(secret) < 32 or not isinstance(authorization, str) or len(authorization) > 300 or not hmac.compare_digest(authorization, "Bearer "+secret):
        raise APIError(401, "Enter the local access key to connect")


class BoundedServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 8

    def __init__(self, address, handler):
        self.capacity = threading.BoundedSemaphore(8)
        super().__init__(address, handler)

    def process_request(self, request, client_address):
        if not self.capacity.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.capacity.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.capacity.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "NetSentinel"
    sys_version = ""
    protocol_version = "HTTP/1.0"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *args):
        pass  # Never log Authorization, bodies, URLs or private inventories.

    def reply(self, status, value, kind="application/json", filename=None):
        body = json.dumps(value, allow_nan=False).encode() if kind == "application/json" else value
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        if self.headers.get("Transfer-Encoding") or self.headers.get_all("Content-Length", []) == []:
            raise APIError(400, "A bounded Content-Length is required")
        if len(self.headers.get_all("Content-Length")) != 1 or self.headers.get("Content-Type") != "application/json":
            raise APIError(400, "JSON request required")
        try:
            size = int(self.headers["Content-Length"])
        except ValueError:
            raise APIError(400, "Invalid request size") from None
        if not 2 <= size <= 16384:
            raise APIError(413, "Request too large")
        try:
            value = json.loads(self.rfile.read(size))
        except (ValueError, UnicodeError):
            raise APIError(400, "Invalid JSON") from None
        if not isinstance(value, dict):
            raise APIError(400, "JSON object required")
        return value

    def dispatch(self):
        try:
            self.handle_api()
        except APIError as exc:
            self.reply(exc.status, {"error": exc.message})
        except (ValueError, KeyError):
            self.reply(400, {"error": "Invalid or unavailable selection"})
        except Exception:
            self.reply(503, {"error": "Operation unavailable. Check the local companion and Windows permissions."})

    do_GET = dispatch
    do_POST = dispatch
