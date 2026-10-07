"""Optional narrow elevated broker: fixed actions and independently observed IDs."""
import re
import threading
import time
import urllib.request
import urllib.error
import json

from .http_boundary import APIError, Handler, BoundedServer, authorize
from .identity import executable_id, protected
from .windows_security import SecurityProvider


class BrokerClient:
    def __init__(self, token=None, port=8766):
        self.token, self.port = token, port

    def call(self, action, values=None):
        if not self.token:
            raise APIError(503, "Privileged broker is disconnected. Start it explicitly to enable controls.")
        body = json.dumps(values or {}).encode()
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/{action}", data=body,
                                         headers={"Authorization": "Bearer "+self.token, "Content-Type": "application/json"})
        try:
            # No ambient proxy, redirects or cloud transport.
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *args):
                    return None
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
            with opener.open(request, timeout=25) as response:
                payload = response.read(262145)
                if len(payload) > 262144:
                    raise APIError(503, "Broker reply exceeded limit")
                return json.loads(payload)
        except (OSError, ValueError):
            raise APIError(503, "Broker unavailable or request refused; existing Windows operations may continue") from None


class Broker:
    def __init__(self, firewall=None, security=None):
        if firewall is None:
            from .firewall import FirewallController
            firewall = FirewallController()
        self.firewall = firewall
        self.security = security or SecurityProvider()
        self.lock = threading.RLock()
        self.lease = time.monotonic()
        self.closed = threading.Event()

    def resolve(self, app):
        if not isinstance(app, str) or not re.fullmatch("[a-f0-9]{64}", app):
            raise ValueError("Invalid observed executable ID")
        import psutil
        for process in psutil.process_iter(["exe"]):
            path = process.info.get("exe")
            try:
                if path and executable_id(path) == app:
                    if protected(path):
                        raise APIError(403, "System and companion executables are protected")
                    return path
            except (ValueError, psutil.Error):
                continue
        raise APIError(409, "The executable must be running and independently observable to block it")

    def action(self, action, data):
        with self.lock:
            allowed = {"heartbeat": set(), "rules": set(), "cleanup": set(), "scan-status": set(), "status": set(), "block": {"app"}, "unblock": {"app"}, "scan": {"kind", "consent"}}
            if action not in allowed or set(data) != allowed[action]:
                raise APIError(400, "Unsupported broker action or fields")
            if action == "heartbeat":
                self.lease = time.monotonic()
                return {"connected": True}
            if action == "block":
                return self.firewall.block(self.resolve(data["app"]), data["app"])
            if action == "unblock":
                return self.firewall.unblock(data["app"])
            if action == "cleanup":
                return self.firewall.cleanup()
            if action == "rules":
                return self.firewall.rules()
            if action == "status":
                return self.security.status()
            if action == "scan-status":
                return self.security.scan_status()
            if data["consent"] is not True or data["kind"] not in {"quick", "full"}:
                raise APIError(400, "Explicit quick/full scan consent required")
            return self.security.start_scan(data["kind"])

    def watchdog(self):
        while not self.closed.wait(5):
            if time.monotonic()-self.lease > 30:
                with self.lock:
                    try:
                        self.firewall.cleanup()
                    except Exception:
                        pass  # API cleanup/rules reports failures; retry on next lease check.


def serve_broker(token, port=8766):
    if not token or len(token) < 32:
        raise ValueError("A separate broker key of at least 32 characters is required")
    broker = Broker()
    result = broker.firewall.cleanup()  # Recovery removes only verified owned rules.
    if result.get("success") is not True:
        raise RuntimeError("Owned-rule recovery failed; inspect Windows Firewall before starting")

    class BrokerHandler(Handler):
        def handle_api(self):
            authorize(self.client_address[0], self.headers.get_all("Host", []), self.headers.get("Origin"), port,
                      self.headers.get("Authorization"), token, self.command, broker=True)
            if self.command != "POST" or not re.fullmatch("/[a-z-]+", self.path):
                raise APIError(404, "Unknown broker operation")
            data = self.body()
            if self.path == "/shutdown":
                if data:
                    raise APIError(400, "Shutdown accepts no fields")
                self.reply(200, {"shutdown_requested": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self.reply(200, broker.action(self.path[1:], data))

    watcher = threading.Thread(target=broker.watchdog, daemon=True)
    server = BoundedServer(("127.0.0.1", port), BrokerHandler)
    watcher.start()
    try:
        server.serve_forever(poll_interval=.3)
    finally:
        broker.closed.set()
        server.server_close()
        broker.firewall.cleanup()
