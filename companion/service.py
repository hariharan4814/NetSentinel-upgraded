"""Unprivileged local companion application. Native privileges live in the broker."""
import math
from pathlib import Path
import re
import threading
import time

from .broker import BrokerClient
from .collector import Collector, adapters
from .http_boundary import Handler, BoundedServer, APIError, authorize
from .store import Store
from .windows_security import SecurityProvider


class Companion:
    def __init__(self, store, broker=None, collector=None, security=None):
        self.store = store
        self.broker = broker or BrokerClient()
        self.collector = collector or Collector(store)
        self.security = security or SecurityProvider()
        self.security_cache = None
        self.scan_cache = None
        self.controls = {}
        self.applied = set()
        self.lock = threading.RLock()
        self.closed = threading.Event()
        self.broker_connected = False
        self.next_retry = {}
        self.next_discovery = 0

    def reconcile(self):
        """An explicit enforcement switch gates all blocking, including manual intent."""
        with self.lock:
            snapshot = self.store.snapshot()
            desired = {app["id"] for app in snapshot["apps"] if app["should_block"]} if self.store.setting("enforcement", False) else set()
            try:
                self.broker.call("heartbeat")
                observed = self.broker.call("rules")
                if observed.get("success") is not True:
                    raise APIError(503, "Cannot reconcile Windows rules")
                self.broker_connected = True
            except APIError:
                self.broker_connected = False
                # Preserve uncertainty until Windows can be queried again.
                for app in desired | self.applied:
                    self.controls[app] = {"success": False, "state": "broker_unavailable", "traffic_blocking_verified": False}
                return
            directions = {}
            for rule in observed.get("rules", []):
                app_id = rule.get("app_id")
                if isinstance(app_id, str) and re.fullmatch("[a-f0-9]{64}", app_id):
                    directions.setdefault(app_id, set())
                    if rule.get("enabled") is True and rule.get("action") == "Block":
                        directions[app_id].add(rule.get("direction"))
            # Reconcile against actual owned rules, including partial rule pairs.
            # Broker restart/lease expiry may remove rules independently of us.
            self.applied = {app for app, present in directions.items() if {"Inbound", "Outbound"} <= present}
            for app in desired | set(directions):
                action = "block" if app in desired else "unblock"
                if action == "block" and app in self.applied:
                    self.controls[app] = {"success": True, "state": "applied_not_traffic_verified", "traffic_blocking_verified": False}
                    continue
                if self.next_retry.get((app, action), 0) > time.monotonic():
                    continue
                try:
                    result = self.broker.call(action, {"app": app})
                except APIError:
                    result = {"success": False, "state": "request_failed", "traffic_blocking_verified": False}
                self.controls[app] = result
                if result.get("success") is True:
                    if action == "block":
                        self.applied.add(app)
                    else:
                        self.applied.discard(app)
                    self.store.event("control", action+"_applied", "Owned firewall rule " + action + " succeeded. Traffic blocking has not been verified.", app)
                else:
                    self.next_retry[(app, action)] = time.monotonic()+30
                    self.store.event("control", action+"_failed", "Windows rule action failed or is unconfirmed; review the broker and permissions.", app)

    def worker(self):
        while not self.closed.wait(2):
            try:
                if time.monotonic() >= self.next_discovery:
                    from .attribution import socket_snapshot
                    discovered = socket_snapshot()
                    for path in {owner.executable for owner in discovered.owners if owner.executable}:
                        self.store.discover(path)
                    self.next_discovery = time.monotonic()+10
                self.reconcile()
            except Exception:
                self.broker_connected = False

    def snapshot(self):
        value = self.store.snapshot()
        value.update(capture=self.collector.view(), enforcement=self.store.setting("enforcement", False),
                     controls=dict(self.controls), broker_connected=self.broker_connected,
                     security=self.security_cache, scan=self.scan_cache)
        return value

    def action(self, action, data):
        fields = {"policy": {"app", "changes"}, "control": {"app", "action"}, "enforcement": {"enabled", "consent"},
                  "capture-start": {"interface", "consent"}, "capture-stop": set(), "security": set(),
                  "scan": {"kind", "consent"}, "scan-status": set(), "cleanup": set(), "report": {"sections", "start", "end", "include_sensitive"}}
        if action not in fields or set(data) != fields[action]:
            raise APIError(400, "Unsupported action or fields")
        with self.lock:
            if action == "policy":
                self.store.policy(data["app"], data["changes"])
            elif action == "control":
                if data["action"] not in {"block", "unblock", "override"}:
                    raise ValueError("Invalid control")
                if data["action"] == "block" and not self.store.setting("enforcement", False):
                    raise APIError(409, "Enable enforcement explicitly before requesting a block")
                self.store.control(data["app"], data["action"])
            elif action == "enforcement":
                if type(data["enabled"]) is not bool or data["consent"] is not True:
                    raise ValueError("Explicit enforcement choice required")
                if data["enabled"]:
                    self.broker.call("heartbeat")
                else:
                    # Record observation-only intent even if broker is unreachable.
                    self.store.set_setting("enforcement", False)
                    try:
                        result = self.broker.call("cleanup")
                        if result.get("success") is not True:
                            raise APIError(503, "Owned rule cleanup failed; run broker recovery")
                        self.applied.clear()
                    except APIError:
                        self.store.event("control", "cleanup_unconfirmed", "Enforcement disabled but cleanup is unconfirmed; run broker recovery.")
                        raise
                self.store.set_setting("enforcement", data["enabled"])
                self.store.event("control", "enforcement_changed", "Operator set enforcement " + ("on" if data["enabled"] else "off"))
            elif action == "capture-start":
                if type(data["interface"]) is not str or data["interface"] not in {a["name"] for a in adapters()}:
                    raise ValueError("Choose an available local adapter")
                try:
                    self.collector.start(data["interface"], data["consent"])
                except RuntimeError:
                    raise APIError(409, "Capture unavailable. Check the separately installed Npcap driver, adapter and capture permissions. No observation was fabricated.") from None
            elif action == "capture-stop":
                self.collector.stop()
            elif action == "security":
                self.security_cache = self.security.status()
                return self.security_cache
            elif action == "scan":
                if data["consent"] is not True or data["kind"] not in {"quick", "full"}:
                    raise ValueError("Explicit scan choice required")
                result = self.broker.call("scan", data)
                self.store.event("control", "scan_requested", data["kind"].title()+" scan requested through Microsoft Defender.")
                return result
            elif action == "scan-status":
                try:
                    self.scan_cache = self.broker.call("scan-status")
                except APIError:
                    self.scan_cache = self.security.scan_status()
                return self.scan_cache
            elif action == "cleanup":
                self.store.set_setting("enforcement", False)
                result = self.broker.call("cleanup")
                if result.get("success") is True:
                    self.applied.clear()
                self.store.event("control", "cleanup", "Owned-rule cleanup " + ("succeeded" if result.get("success") else "failed"))
                return result
            elif action == "report":
                from .reports import create_report
                if not isinstance(data["sections"], list) or not 1 <= len(data["sections"]) <= 4 or set(data["sections"]) - {"usage", "connections", "security", "actions"} or type(data["include_sensitive"]) is not bool:
                    raise ValueError("Invalid report options")
                if any(type(data[key]) not in {int, float} or not math.isfinite(data[key]) for key in ("start", "end")) or data["start"] > data["end"]:
                    raise ValueError("Invalid report dates")
                snapshot = self.store.snapshot(start=data["start"], end=data["end"])
                snapshot.update(capture=self.collector.view(), security=self.security_cache, scan=self.scan_cache)
                return create_report(snapshot, data["sections"], data["include_sensitive"])
            self.reconcile()
            return {"success": True, "controls": dict(self.controls), "broker_connected": self.broker_connected}

    def stop(self):
        self.closed.set()
        self.collector.stop()
        try:
            result = self.broker.call("cleanup")
            if result.get("success") is not True:
                raise APIError(503, "cleanup failed")
        except APIError:
            if self.store.setting("enforcement", False):
                self.store.event("control", "shutdown_cleanup_unconfirmed", "Run elevated broker recovery to confirm owned-rule cleanup.")


def make_server(app, token, port=8765):
    static = Path(__file__).parent / "web"

    class CompanionHandler(Handler):
        def handle_api(self):
            # Even unauthenticated assets reject hostile Host and Origin values.
            authorize(self.client_address[0], self.headers.get_all("Host", []), self.headers.get("Origin"), port,
                      "Bearer "+token, token, self.command)
            if self.command == "GET" and self.path in {"/", "/app.js", "/style.css"}:
                name, kind = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}[self.path]
                self.reply(200, (static/name).read_bytes(), kind)
                return
            authorize(self.client_address[0], self.headers.get_all("Host", []), self.headers.get("Origin"), port,
                      self.headers.get("Authorization"), token, self.command)
            if self.command == "GET" and self.path == "/api/state":
                self.reply(200, app.snapshot())
            elif self.command == "GET" and self.path == "/api/adapters":
                self.reply(200, {"adapters": adapters()})
            elif self.command == "POST" and re.fullmatch("/api/[a-z-]+", self.path):
                action = self.path[5:]
                data = self.body()
                if action == "shutdown":
                    if data:
                        raise APIError(400, "Shutdown accepts no fields")
                    self.reply(200, {"shutdown_requested": True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                result = app.action(action, data)
                if action == "report":
                    self.reply(200, result, "application/pdf", "NetSentinel-local-report.pdf")
                else:
                    self.reply(200, result)
            else:
                raise APIError(404, "Unknown local endpoint")

    return BoundedServer(("127.0.0.1", port), CompanionHandler)
