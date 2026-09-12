"""Opt-in diagnostic launcher; independently records the capture process's exit.

Creates private text-only artifacts in ignored tmp/. Never an acceptance runner.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4
import psutil


def exit_fields(returncode):
    unsigned = returncode & 0xffffffff
    return {"child_returncode": returncode, "exit_unsigned": unsigned,
            "exit_signed": unsigned if unsigned < 2**31 else unsigned - 2**32,
            "exit_hex": f"0x{unsigned:08X}"}


def stop_child_tree(child):
    # Windows venv python.exe can launch a base-interpreter child. Do not leave
    # that owned capture process orphaned when the observer cancels its launcher.
    try:
        descendants = psutil.Process(child.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        descendants = []
    for process in reversed(descendants):
        try:
            process.kill()
        except psutil.NoSuchProcess:
            pass
    if child.poll() is None:
        child.kill()


def observe(command, directory, timeout):
    """Child stdout/stderr go directly to files; no pipe buffers or shell."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    def record(event):
        event = {"observed_at": time.time(), "observer_pid": os.getpid(), **event}
        with (directory / "observer.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps(event) + "\n")
        print(json.dumps(event), flush=True)

    with (directory / "stdout.jsonl").open("xb") as stdout, (directory / "stderr.txt").open("xb") as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                 shell=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        record({"type": "observer_started", "child_pid": child.pid,
                "artifacts": str(directory.resolve()), "timeout_seconds": timeout})
        observer_action = None
        try:
            code = child.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            # Explicit observer intervention must never be mistaken for a native crash.
            observer_action = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "operator_interrupt"
            record({"type": "observer_termination_requested", "child_pid": child.pid,
                    "reason": observer_action})
            stop_child_tree(child)
            code = child.wait(timeout=5)
    summary_present = False
    last_event = None
    with (directory / "stdout.jsonl").open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            summary_present |= event.get("type") == "stability_summary"
            last_event = {k: event[k] for k in ("type", "observed_at", "run_elapsed_seconds", "phase") if k in event}
    result = {"type": "observer_child_exited", "child_pid": child.pid, **exit_fields(code),
              "wall_seconds": time.monotonic() - started, "observer_action": observer_action,
              "final_summary_present": summary_present, "last_stdout_event": last_event}
    record(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--diagnostic-seconds", type=int, choices=range(5, 1801), default=480, metavar="5..1800")
    parser.add_argument("--recovery-retry-seconds", type=float, default=2)
    parser.add_argument("--recovery-timeout-seconds", type=float, default=30)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = root / "tmp" / f"stability-process-{stamp}-{uuid4().hex[:8]}"
    command = [sys.executable, "-u", "-X", "faulthandler", str(Path(__file__).with_name("stability_live.py")),
               "--interface", args.interface, "--diagnostic-seconds", str(args.diagnostic_seconds),
               "--recovery-retry-seconds", str(args.recovery_retry_seconds),
               "--recovery-timeout-seconds", str(args.recovery_timeout_seconds),
               "--process-diagnostics-dir", str(directory)]
    observe(command, directory, timeout=args.diagnostic_seconds + 90)
    return 2  # Diagnostic only; raw child status is preserved in observer.jsonl.


if __name__ == "__main__":
    raise SystemExit(main())
