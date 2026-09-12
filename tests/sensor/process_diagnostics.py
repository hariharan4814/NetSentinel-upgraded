"""Opt-in process evidence, without packets, frame locals or memory dumps."""
import atexit
import faulthandler
import json
import os
from pathlib import Path
import sys
import threading
import time


class ProcessDiagnostics:
    def __init__(self, directory, diagnostics):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.journal = (self.directory / "process.jsonl").open("x", encoding="utf-8", buffering=1)
        self.faults = (self.directory / "faults.txt").open("x", encoding="utf-8")
        self.diagnostics = diagnostics
        self.lock = threading.Lock()
        self.old_thread_hook = threading.excepthook
        self.faults_were_enabled = faulthandler.is_enabled()
        self.closed = False
        faulthandler.enable(file=self.faults, all_threads=True)
        threading.excepthook = self.thread_exception
        atexit.register(self.on_exit)
        self.write({"type": "process_started", "parent_pid": os.getppid(),
                    "python": sys.version, "executable": sys.executable})

    def write(self, record):
        with self.lock:
            self.journal.write(json.dumps({"pid": os.getpid(), "recorded_at": time.time(),
                                           "native_thread_id": threading.get_native_id(),
                                           "elapsed_seconds": time.monotonic() - (
                                               self.diagnostics.started if self.diagnostics.started is not None
                                               else self.diagnostics.origin),
                                           "phase": self.diagnostics.phase(), **record}) + "\n")
            self.journal.flush()

    def observe(self, record):
        # Whitelist operational breadcrumbs; never copy flow/endpoints/packet repr.
        if record["type"] == "window":
            return
        allowed = ("type", "state", "reason", "session_id", "run_id", "observed_at",
                   "run_elapsed_seconds", "phase", "valid", "interface_losses",
                   "monitoring_gap_seconds", "step", "worker_alive", "worker_running",
                   "shutdown_error", "shutdown_seconds")
        self.write({k: record[k] for k in allowed if k in record})

    def thread_exception(self, args):
        try:
            # The diagnostic object stores formatted strings, never thread/frame references.
            self.diagnostics.record(args.exc_value, source="uncaught_thread")
        finally:
            self.old_thread_hook(args)

    def on_exit(self):
        try:
            self.write({"type": "interpreter_atexit"})
        finally:
            self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        atexit.unregister(self.on_exit)
        threading.excepthook = self.old_thread_hook
        faulthandler.disable()
        if self.faults_were_enabled:
            faulthandler.enable(all_threads=True)  # Restore startup stderr handler.
        self.faults.close()
        self.journal.close()
