"""Versioned bounded local state; UTC daily buckets and separate provenance."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
import sqlite3
import threading
import time

from .identity import canonical, executable_id, protected

MODES = {"LIVE", "SIMULATION", "REPLAY"}


def utc_day(at):
    return datetime.fromtimestamp(at, timezone.utc).strftime("%Y-%m-%d")


def reset_times(at):
    dt = datetime.fromtimestamp(at, timezone.utc)
    daily = dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    monthly = daily.replace(day=1)
    if monthly <= dt:
        monthly = monthly.replace(year=monthly.year + 1, month=1) if monthly.month == 12 else monthly.replace(month=monthly.month + 1)
    return daily.timestamp(), monthly.timestamp()


class Store:
    def __init__(self, path, clock=time.time):
        self.clock, self.lock = clock, threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=3000")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in {0, 1}:
            raise ValueError("Unsupported companion schema; back up state before upgrading")
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS apps(id TEXT PRIMARY KEY,path TEXT NOT NULL,name TEXT NOT NULL,protected INTEGER NOT NULL,seen REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS usage(app TEXT NOT NULL,day TEXT NOT NULL,mode TEXT NOT NULL,up INTEGER NOT NULL,down INTEGER NOT NULL,PRIMARY KEY(app,day,mode));
        CREATE TABLE IF NOT EXISTS policies(app TEXT PRIMARY KEY REFERENCES apps(id),daily INTEGER,monthly INTEGER,warning INTEGER NOT NULL DEFAULT 80,direction TEXT NOT NULL DEFAULT 'combined',auto INTEGER NOT NULL DEFAULT 0,override REAL NOT NULL DEFAULT 0,manual INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,at REAL NOT NULL,app TEXT,category TEXT NOT NULL,code TEXT NOT NULL,message TEXT NOT NULL,mode TEXT NOT NULL,marker TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS flows(id INTEGER PRIMARY KEY,app TEXT,at REAL NOT NULL,protocol TEXT NOT NULL,remote TEXT NOT NULL,port INTEGER,up INTEGER NOT NULL,down INTEGER NOT NULL,mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS destinations(app TEXT,remote TEXT,mode TEXT,at REAL,PRIMARY KEY(app,remote,mode));
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        PRAGMA user_version=1;
        ''')
        self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    def setting(self, key, default=None):
        with self.lock:
            row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else default

    def set_setting(self, key, value):
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value)))

    def discover(self, path, at=None):
        path, at = canonical(path), self.clock() if at is None else at
        app = executable_id(path)
        with self.lock, self.db:
            exists = self.db.execute("SELECT 1 FROM apps WHERE id=?", (app,)).fetchone()
            if not exists and self.db.execute("SELECT count(*) FROM apps").fetchone()[0] >= 512:
                return None
            self.db.execute("INSERT INTO apps VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET seen=excluded.seen, protected=excluded.protected",
                            (app, path, path.rsplit('\\', 1)[-1], int(protected(path)), at))
            self.db.execute("INSERT OR IGNORE INTO policies(app) VALUES (?)", (app,))
        return app

    def event(self, category, code, message, app=None, mode="LIVE", marker=None, at=None):
        if mode not in MODES:
            raise ValueError("Invalid provenance")
        with self.lock, self.db:
            self.db.execute("INSERT OR IGNORE INTO events(at,app,category,code,message,mode,marker) VALUES (?,?,?,?,?,?,?)",
                            (self.clock() if at is None else at, app, category, code, message[:512], mode, marker))
            self.db.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 2000)")

    def record(self, records, mode="LIVE"):
        """Batch (app_id-or-None, PacketMetadata), already attributed by collector."""
        if mode not in MODES or len(records) > 8192:
            raise ValueError("Invalid ingestion batch")
        now, totals, flows = self.clock(), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        for app, packet in records:
            if not math.isfinite(packet.timestamp) or packet.timestamp > now + 5 or packet.timestamp < now - 90 * 86400:
                continue
            direction = 0 if packet.direction == "outbound" else 1
            if packet.direction not in {"inbound", "outbound"}:
                app = None
            key = (app or "unassigned", utc_day(packet.timestamp), mode)
            totals[key][direction] += packet.packet_length
            if packet.protocol in {"TCP", "UDP"} and packet.direction in {"outbound", "inbound"}:
                remote, port = (packet.destination_ip, packet.destination_port) if direction == 0 else (packet.source_ip, packet.source_port)
                flows[(app, int(packet.timestamp), packet.protocol, remote, port, mode)][direction] += packet.packet_length
        with self.lock, self.db:
            for key, (up, down) in totals.items():
                self.db.execute("INSERT INTO usage VALUES (?,?,?,?,?) ON CONFLICT(app,day,mode) DO UPDATE SET up=up+excluded.up,down=down+excluded.down", (*key, up, down))
            for (app, at, protocol, remote, port, provenance), (up, down) in flows.items():
                self.db.execute("INSERT INTO flows(app,at,protocol,remote,port,up,down,mode) VALUES (?,?,?,?,?,?,?,?)", (app, at, protocol, remote, port, up, down, provenance))
                if app and up:
                    known = self.db.execute("SELECT 1 FROM destinations WHERE app=? AND remote=? AND mode=?", (app, remote, provenance)).fetchone()
                    count = self.db.execute("SELECT count(*) FROM destinations WHERE app=? AND mode=?", (app, provenance)).fetchone()[0]
                    if not known and count >= 5:
                        self.event("security", "new_destination", "Destination not previously seen in retained outbound history; a normal update or website may explain it.", app, provenance, f"dest:{app}:{remote}:{provenance}:{utc_day(at)}", at)
                    self.db.execute("INSERT OR REPLACE INTO destinations VALUES (?,?,?,?)", (app, remote, provenance, at))
            # Heuristics describe only measured evidence; no intent or malware verdict.
            for app in {k[0] for k in flows if k[0]}:
                recent = self.db.execute("SELECT sum(up),count(DISTINCT remote || ':' || port) FROM flows WHERE app=? AND mode=? AND at>=?", (app, mode, now - 60)).fetchone()
                if recent[0] and recent[0] >= 100 * 1024 * 1024:
                    self.event("security", "outbound_volume", "At least 100 MiB outbound IP bytes observed in 60 seconds; uploads/backups may explain it (rule v1).", app, mode, f"volume:{app}:{mode}:{int(now//60)}")
                if recent[1] >= 40:
                    self.event("security", "destination_burst", "At least 40 distinct outbound/inbound remote endpoints observed in 60 seconds; browsers may explain it (rule v1).", app, mode, f"burst:{app}:{mode}:{int(now//60)}")
            self.prune(now)

    def prune(self, now=None):
        now = self.clock() if now is None else now
        self.db.execute("DELETE FROM usage WHERE day<?", (utc_day(now-90*86400),))
        self.db.execute("DELETE FROM flows WHERE at<? OR id NOT IN (SELECT id FROM flows ORDER BY id DESC LIMIT 10000)", (now-7*86400,))
        self.db.execute("DELETE FROM events WHERE at<?", (now-90*86400,))
        self.db.execute("DELETE FROM destinations WHERE at<? OR rowid NOT IN (SELECT rowid FROM destinations ORDER BY at DESC LIMIT 5000)", (now-30*86400,))

    def policy(self, app, changes):
        allowed = {"daily", "monthly", "warning", "direction", "auto"}
        if not isinstance(changes, dict) or set(changes) - allowed:
            raise ValueError("Unknown quota fields")
        for key in ("daily", "monthly"):
            if key in changes and changes[key] is not None and (type(changes[key]) is not int or not 1024 <= changes[key] <= 10**15):
                raise ValueError("Quota must be null or 1 KiB to 1 PB in bytes")
        if "warning" in changes and (type(changes["warning"]) is not int or not 1 <= changes["warning"] <= 100):
            raise ValueError("Warning must be 1-100 percent")
        if "direction" in changes and changes["direction"] not in {"upload", "download", "combined"}:
            raise ValueError("Invalid quota direction")
        if "auto" in changes and type(changes["auto"]) is not bool:
            raise ValueError("Automatic blocking requires explicit true/false")
        with self.lock, self.db:
            row = self.db.execute("SELECT protected FROM apps WHERE id=?", (app,)).fetchone()
            if not row:
                raise ValueError("Unknown observed application")
            if row[0] and changes.get("auto"):
                raise ValueError("Critical/companion executables cannot be blocked")
            for key, value in changes.items():
                self.db.execute(f"UPDATE policies SET {key}=? WHERE app=?", (value, app))
        self.event("control", "quota_updated", "Quota settings changed by local operator.", app)

    def control(self, app, action):
        with self.lock, self.db:
            row = self.db.execute("SELECT a.protected,p.daily,p.monthly FROM apps a JOIN policies p ON a.id=p.app WHERE a.id=?", (app,)).fetchone()
            if not row or (row[0] and action == "block"):
                raise ValueError("Unknown or protected executable")
            if action == "block":
                self.db.execute("UPDATE policies SET manual=1,override=0 WHERE app=?", (app,))
            elif action in {"unblock", "override"}:
                daily, monthly = reset_times(self.clock())
                # Override each enabled quota until its nearest upcoming reset.
                until = min([v for v, enabled in ((daily, row[1]), (monthly, row[2])) if enabled] or [daily])
                self.db.execute("UPDATE policies SET manual=0,override=? WHERE app=?", (until, app))
            else:
                raise ValueError("Unknown control action")
        self.event("control", action, "Local operator requested " + action + ". Rule application is reported separately.", app)

    def snapshot(self, mode="LIVE", start=None, end=None):
        if mode not in MODES:
            raise ValueError("Invalid provenance")
        now = self.clock()
        day, month = utc_day(now), utc_day(now)[:7]
        daily_reset, monthly_reset = reset_times(now)
        with self.lock, self.db:
            self.prune(now)
            apps = []
            for row in self.db.execute("SELECT a.*,p.daily,p.monthly,p.warning,p.direction,p.auto,p.override,p.manual FROM apps a JOIN policies p ON a.id=p.app ORDER BY a.seen DESC"):
                app = dict(row)
                for name, prefix in (("today", day), ("month", month)):
                    values = self.db.execute("SELECT coalesce(sum(up),0),coalesce(sum(down),0),count(*) FROM usage WHERE app=? AND mode=? AND day LIKE ?", (app["id"], mode, prefix+"%")).fetchone()
                    app[name] = {"uploaded": values[0], "downloaded": values[1], "combined": values[0]+values[1], "observed": values[2] > 0}
                reached = []
                metric = {"upload": "uploaded", "download": "downloaded", "combined": "combined"}[app["direction"]]
                for field, bucket, period in (("daily", "today", day), ("monthly", "month", month)):
                    limit, used = app[field], app[bucket][metric]
                    if limit:
                        if used >= limit:
                            reached.append(field)
                        if used * 100 >= limit * app["warning"]:
                            self.event("quota", "quota_reached" if used >= limit else "quota_warning", f"{field.title()} quota: observed {used} of {limit} bytes ({metric}). Approximate, not billable usage.", app["id"], mode,
                                       f"quota:{app['id']}:{mode}:{field}:{period}:{limit}:{'reached' if used >= limit else 'warning'}")
                app["reached"] = reached
                app["should_block"] = bool(mode == "LIVE" and not app["protected"] and (app["manual"] or (app["auto"] and reached and app["override"] <= now)))
                apps.append(app)
            start = max(now-90*86400, start if start is not None else now-7*86400)
            end = min(now, end if end is not None else now)
            usage = [dict(r) for r in self.db.execute("SELECT * FROM usage WHERE mode=? AND day>=? AND day<=? ORDER BY day,app", (mode, utc_day(start), utc_day(end)))]
            flows = [dict(r) for r in self.db.execute("SELECT * FROM flows WHERE mode=? AND at>=? AND at<=? ORDER BY at DESC LIMIT 500", (mode, start, end))]
            events = [dict(r) for r in self.db.execute("SELECT at,app,category,code,message,mode FROM events WHERE mode=? AND at>=? AND at<=? ORDER BY at DESC LIMIT 500", (mode, start, end))]
            unassigned = self.db.execute("SELECT coalesce(sum(up+down),0) FROM usage WHERE app='unassigned' AND mode=? AND day=?", (mode, day)).fetchone()[0]
        return {"schema": "companion-v1", "mode": mode, "generated_at": now, "reset_timezone": "UTC", "daily_reset": daily_reset, "monthly_reset": monthly_reset,
                "apps": apps, "flows": flows, "events": events, "usage": usage, "unassigned_today": unassigned, "period": {"start": start, "end": end},
                "limits": "Approximate packet/socket matching; observed IP bytes, not ISP billing. Retention: usage 90 days; observed flows 7 days/10,000; events 90 days/2,000. Returned flows/events capped at 500. Missing capture is not zero usage."}
