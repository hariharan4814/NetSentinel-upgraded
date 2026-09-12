"""Explicit 30-minute own-host validation; no payload or flow endpoint output.

Keep the laptop idle for the first 5 minutes. Minutes 5-10 send one ordinary
HTTP HEAD every 5 seconds to 1.1.1.1:80, bound to the selected interface IPv4.
Use normally for the final 20 minutes; keep it awake and the adapter connected.
Exception diagnostics contain messages and tracebacks without frame locals;
keep redirected output local in ignored tmp/ and review before sharing.
"""
import argparse
import json
import math
from pathlib import Path
import socket
import sys
import threading
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sensor.capture import local_addresses, run_capture


def p95(values):
    return sorted(values)[math.ceil(.95 * len(values))-1] if values else None


class Diagnostics:
    """Local exception evidence only; never serialize frame locals or packets."""
    def __init__(self):
        self.origin = time.monotonic()
        self.started = None
        self.stage = "preflight"
        self.failure = None
        self.process = None

    def phase(self):
        if self.started is None:
            return "preflight"
        elapsed = time.monotonic() - self.started
        return "low_idle" if elapsed < 300 else "controlled" if elapsed < 600 else "normal"

    def record(self, exc, *, source, fatal=True):
        record = {"type": "validation_exception", "exception_type": type(exc).__name__,
                  "exception_message": str(exc),
                  "traceback": "".join(traceback.TracebackException.from_exception(
                      exc, capture_locals=False).format()),
                  "phase": self.phase(), "stage": source,
                  "elapsed_seconds": time.monotonic() - (
                      self.started if self.started is not None else self.origin)}
        if fatal and self.failure is None:
            self.failure = record
        if self.process is not None:
            self.process.write(record)
        try:
            print(json.dumps(record), flush=True)
        except (OSError, ValueError):
            # A broken/closed stdout must not hide the original exception.
            print(json.dumps(record), file=sys.stderr, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True)
    short_run = parser.add_mutually_exclusive_group()
    short_run.add_argument("--smoke-seconds", type=int, choices=range(5, 61), help="instrumentation check only; never a 30-minute PASS")
    short_run.add_argument("--diagnostic-seconds", type=int, choices=range(5, 1801), metavar="5..1800",
                           help="bounded diagnostic with original phase schedule; never an acceptance PASS")
    parser.add_argument("--recovery-retry-seconds", type=float, default=2)
    parser.add_argument("--recovery-timeout-seconds", type=float, default=30)
    parser.add_argument("--process-diagnostics-dir", type=Path,
                        help="private local directory for fault traces and process breadcrumbs")
    args = parser.parse_args()
    diagnostics = Diagnostics()
    if args.process_diagnostics_dir:
        from process_diagnostics import ProcessDiagnostics
        diagnostics.process = ProcessDiagnostics(args.process_diagnostics_dir, diagnostics)
    try:
        result = validate(args, diagnostics)
    except Exception as exc:
        diagnostics.record(exc, source=diagnostics.stage)
        result = 2
    except BaseException as exc:
        # SystemExit/KeyboardInterrupt are outside Exception. Preserve their exit semantics.
        diagnostics.record(exc, source=diagnostics.stage)
        raise
    if diagnostics.process is not None:
        diagnostics.process.write({"type": "validator_returned", "exit_code": result})
    return result


def validate(args, diagnostics):
    duration = args.diagnostic_seconds or args.smoke_seconds or 1800
    local = next((a for a in local_addresses(args.interface) if ":" not in a), None)
    if local is None:
        print(json.dumps({"type": "validation_error", "reason": "selected interface IPv4 unavailable", "passed": False}))
        return 2
    ready, stop = threading.Event(), threading.Event()
    capture_running = [True]
    # Finite run and sampling/retry cadences bound histories. Restarted sessions
    # can add partial window finalizations beyond the uninterrupted ~181 windows.
    samples, delays, finalization = [], [], []
    state = {"traffic_attempts": 0, "traffic_successes": 0, "traffic_errors": 0,
             "packets": 0, "ip_bytes": 0, "windows": 0, "interface_losses": 0}
    started = [None]
    stopped = {}

    def traffic():
        if not ready.wait(5):
            return
        if stop.wait(300):
            return
        while time.monotonic() - started[0] < 600 and not stop.is_set():
            if not capture_running[0]:
                stop.wait(1)
                continue
            attempt_start = time.monotonic()
            state["traffic_attempts"] += 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(3)
                    sock.bind((local, 0))
                    sock.connect(("1.1.1.1", 80))
                    sock.sendall(b"HEAD / HTTP/1.1\r\nHost: one.one.one.one\r\nConnection: close\r\n\r\n")
                    if sock.recv(4096).startswith(b"HTTP/"):
                        state["traffic_successes"] += 1
                    else:
                        state["traffic_errors"] += 1
            except OSError as exc:
                state["traffic_errors"] += 1
                diagnostics.record(exc, source="controlled_traffic", fatal=False)
            stop.wait(max(0, 5 - (time.monotonic() - attempt_start)))

    def traffic_worker():
        try:
            traffic()
        except Exception as exc:
            try:
                diagnostics.record(exc, source="controlled_traffic")
            finally:
                stop.set()

    def emit(record):
        nonlocal local
        kind = record["type"]
        if diagnostics.process is not None:
            diagnostics.process.observe(record)
        if kind == "capture_started":
            started[0] = time.monotonic()
            diagnostics.started = started[0]
            ready.set()
            record = {k: v for k, v in record.items() if k != "capture_interface"}
        elif kind == "capture_restarted":
            # Keep the original run/phase clock; refresh the traffic binding.
            local = next((a for a in local_addresses(args.interface) if ":" not in a), None)
            record = {k: v for k, v in record.items() if k != "capture_interface"}
        elif kind == "capture_status":
            capture_running[0] = record["state"] == "RUNNING" and local is not None
            if record["state"] == "INTERFACE_LOST":
                state["interface_losses"] += 1
        elif kind == "window":
            state["windows"] += 1
            state["packets"] += sum(f["packets"] for f in record["flows"])
            state["ip_bytes"] += sum(f["ip_bytes"] for f in record["flows"])
            # Include closed startup windows for timing; exclude shutdown flushes.
            if record["finalized_at"] >= record["end"] + 2:
                finalization.append(record["processed_at"] - record["end"] - 2)
            return
        elif kind == "health":
            elapsed = time.monotonic() - started[0]
            record = {**record, "run_elapsed_seconds": elapsed,
                      "phase": "low_idle" if elapsed < 300 else "controlled" if elapsed < 600 else "normal"}
            samples.append(record)
        elif kind == "capture_stopped":
            stopped.update(record)
            record = {k: v for k, v in record.items() if k != "interface"}
        print(json.dumps(record), flush=True)
        if kind == "health":
            # Time through return of flushed print, not physical screen rendering.
            delays.append(time.time() - record["observed_at"])

    worker = threading.Thread(target=traffic_worker, daemon=True)
    diagnostics.stage = "capture"
    try:
        worker.start()
        run_capture(args.interface, duration, emit, stop_event=stop,
                    recovery_retry_seconds=args.recovery_retry_seconds,
                    recovery_timeout_seconds=args.recovery_timeout_seconds,
                    lifecycle_diagnostics=diagnostics.process is not None)
    except Exception as exc:
        diagnostics.record(exc, source="capture")
    finally:
        returned = time.monotonic()
        stop.set()
        if worker.ident is not None:
            worker.join(timeout=4)
    diagnostics.stage = "validation"
    error = diagnostics.failure["exception_type"] if diagnostics.failure else None
    elapsed = returned - started[0] if started[0] is not None else 0
    checks = {
        "duration": elapsed >= 1800 and not args.smoke_seconds and not args.diagnostic_seconds,
        "controlled_activity": state["traffic_successes"] >= 55 and state["traffic_errors"] == 0,
        "sample_coverage": len(samples) >= 1700 and all(r["valid"] for r in samples),
        "sample_delay": bool(delays) and p95(delays) <= 2,
        "window_delay": bool(finalization) and p95(finalization) <= 1,
        "memory": bool(stopped) and stopped.get("peak_rss_bytes", math.inf) < 500*1024**2,
        "bounds": bool(stopped) and stopped["queue_high_water"] <= 20000 and stopped["flow_high_water"] <= 10000 and stopped["window_high_water"] <= 2,
        "clean_capture": bool(stopped) and not error and not state["interface_losses"] and not stopped.get("interface_losses", 0) and stopped["reason"] == "duration" and not any(stopped[k] for k in ("queue_dropped", "flow_overflow", "late", "parse_errors", "flow_errors", "queue_remaining", "shutdown_error")),
        "conservation": bool(stopped) and state["packets"] == stopped["normalized"],
        "shutdown": bool(stopped) and stopped["shutdown_seconds"] <= 5 and elapsed - duration <= 5,
    }
    summary = {"type": "stability_summary", "run_seconds": elapsed, **state,
               "diagnostic_only": bool(args.smoke_seconds or args.diagnostic_seconds),
               "duration_stop_overrun_seconds": max(0, elapsed - duration),
               "health_samples": len(samples), "sample_interval_p95_seconds": p95([r["elapsed_seconds"] for r in samples]),
               "sample_to_flushed_console_p95_seconds": p95(delays),
               "window_processing_after_lateness_p95_seconds": p95(finalization),
               "checks": checks, "automated_checks_passed": all(checks.values()),
               "idle_phase_requires_operator_review": True,
               "memory_trend_requires_review": True, "error": error,
               "exception": diagnostics.failure,
               "stopped": {k: v for k, v in stopped.items() if k != "interface"}}
    print(json.dumps(summary), flush=True)
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
