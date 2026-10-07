"""Start the isolated local SIMULATION lab; never touches research PostgreSQL.

Run with .venv-lab/Scripts/python.exe scripts/run_ai_lab.py after building frontend.
Secrets are inherited in process environments only and are never printed.
"""
from __future__ import annotations

import argparse
from collections import deque
import getpass
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import psutil

ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A health probe must never carry a local read credential to another URL.
        return None


def valid_password(value: str) -> bool:
    return 32 <= len(value) <= 256 and all(33 <= ord(c) <= 126 for c in value) and not value.startswith("replace-with-")


class LabStack:
    """Own only child processes created by this instance, with bounded log memory."""

    def __init__(self, password: str, *, backend_port=8811, frontend_port=3105, state=None):
        if not valid_password(password):
            raise ValueError("Use a 32-256 character password without spaces (printable ASCII).")
        if backend_port == frontend_port or any(type(p) is not int or not 1024 <= p <= 65535 for p in (backend_port, frontend_port)):
            raise ValueError("Choose distinct unprivileged ports between 1024 and 65535.")
        self.backend_port, self.frontend_port = backend_port, frontend_port
        self.state = Path(state or ROOT / "artifacts/lab/standalone").resolve()
        self.base = f"http://127.0.0.1:{backend_port}"
        self.url = f"http://127.0.0.1:{frontend_port}"
        self.password = password
        self.tokens = {name: secrets.token_hex(32) for name in ("READ", "LAB", "LAB_WORKER")}
        self.children = []
        self.logs = deque(maxlen=200)

    def environment(self):
        # Strip inherited application credentials; each child receives only its scope.
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith(("NETSENTINEL_", "POSTGRES_", "DJANGO_"))
               and key.upper() != "BACKEND_API_BASE_URL"}
        env["PYTHONUNBUFFERED"] = "1"
        return env

    def spawn(self, name, args, env, cwd=ROOT):
        process = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.children.append((process, psutil.Process(process.pid)))
        def drain():
            # Logs are bounded in memory and not emitted (framework errors may contain configuration).
            for line in iter(lambda: process.stdout.readline(1001), ""):
                self.logs.append((name, line[:1000]))
            process.stdout.close()
        threading.Thread(target=drain, daemon=True).start()
        return process

    def wait_http(self, url, process, headers=None, timeout=45):
        deadline = time.monotonic() + timeout
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("A lab process exited during startup; run its documented command for diagnostics.")
            try:
                with opener.open(urllib.request.Request(url, headers=headers or {}), timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.2)
        raise RuntimeError("Lab startup timed out. Check the setup guide and port availability.")

    def start(self):
        python_backend = ROOT / ".venv-backend/Scripts/python.exe"
        python_lab = ROOT / ".venv-lab/Scripts/python.exe"
        node = shutil.which("node")
        next_cli = ROOT / "frontend/node_modules/next/dist/bin/next"
        if not all(p.is_file() for p in (python_backend, python_lab, next_cli, ROOT / "frontend/.next/BUILD_ID")) or not node:
            raise RuntimeError("Setup is incomplete: install the documented environments and build the frontend first.")
        for port in (self.backend_port, self.frontend_port):
            with socket.socket() as probe:
                if os.name == "nt":
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                probe.bind(("127.0.0.1", port))
        self.state.mkdir(parents=True, exist_ok=True)
        backend = self.environment()
        backend.update({f"NETSENTINEL_{scope}_TOKEN": token for scope, token in self.tokens.items()})
        backend.update(DJANGO_SECRET_KEY=secrets.token_hex(40), DJANGO_SETTINGS_MODULE="config.lab_settings",
                       NETSENTINEL_LAB_DATABASE_PATH=str(self.state / "demo.sqlite3"))
        try:
            migration = self.spawn("migration", [python_backend, "manage.py", "migrate", "--noinput", "--settings=config.lab_settings"], backend, ROOT / "backend")
            if migration.wait(timeout=60) != 0:
                raise RuntimeError("Standalone lab migration failed. Existing research storage was not changed.")
            api = self.spawn("api", [python_backend, "manage.py", "runserver", f"127.0.0.1:{self.backend_port}", "--noreload", "--settings=config.lab_settings"], backend, ROOT / "backend")
            self.wait_http(self.base + "/api/v1/lab/jobs/", api, {"Authorization": "Bearer " + self.tokens["READ"]})
            worker_env = self.environment()
            worker_env["NETSENTINEL_LAB_WORKER_TOKEN"] = self.tokens["LAB_WORKER"]
            self.spawn("worker", [python_lab, "-m", "lab.worker", "--base-url", self.base, "--artifact-root", self.state / "experiments"], worker_env)
            web_env = self.environment()
            web_env.update(NETSENTINEL_OPERATOR_PASSWORD=self.password, NETSENTINEL_READ_TOKEN=self.tokens["READ"],
                           NETSENTINEL_LAB_TOKEN=self.tokens["LAB"], BACKEND_API_BASE_URL=self.base + "/api/v1/")
            web = self.spawn("web", [node, next_cli, "start", "--hostname", "127.0.0.1", "--port", str(self.frontend_port)], web_env, ROOT / "frontend")
            self.wait_http(self.url + "/lab", web)
            return self
        except BaseException:
            self.stop()
            raise

    def stop(self):
        owned = []
        for process, identity in reversed(self.children):
            if process.poll() is None:
                try:
                    if identity.is_running():
                        owned.extend(identity.children(recursive=True))
                        owned.append(identity)
                except psutil.NoSuchProcess:
                    pass
        for identity in owned:
            try:
                identity.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(owned, timeout=5)
        for identity in alive:
            try:
                identity.kill()
            except psutil.NoSuchProcess:
                pass
        for process, _ in self.children:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        self.children.clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-port", type=int, default=8811)
    parser.add_argument("--frontend-port", type=int, default=3105)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    password = os.environ.get("NETSENTINEL_OPERATOR_PASSWORD") or getpass.getpass("Choose a local lab password (32-256 characters, no spaces): ")
    stack = None
    try:
        stack = LabStack(password, backend_port=args.backend_port, frontend_port=args.frontend_port).start()
        print(f"NetSentinel AI Lab: {stack.url}/lab\nSIMULATION only. Sign in with your chosen password. Ctrl+C stops this stack.")
        if not args.no_browser:
            webbrowser.open(stack.url + "/lab")
        while True:
            time.sleep(1)
            if any(process.poll() is not None for process, _ in stack.children[1:]):
                raise RuntimeError("A lab process stopped. Restart the stack; interrupted jobs expire through their lease.")
    except KeyboardInterrupt:
        print("Stopping the local lab. Saved experiments remain available on restart.")
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Lab could not continue: {error}")
        return 1
    finally:
        if stack:
            stack.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
