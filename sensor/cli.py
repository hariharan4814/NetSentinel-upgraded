import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import sys
import time
from uuid import uuid4

from .capture import capture_interfaces, run_capture
from .counters import calculate_rates, read_counters
from .interfaces import list_interfaces, select_interface


def emit(record):
    print(json.dumps(record), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standalone metadata sensor feasibility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("interfaces")
    sub.add_parser("capture-interfaces", help="show Windows index/GUID to Npcap mapping")
    counters = sub.add_parser("counters")
    counters.add_argument("--interface", required=True)
    counters.add_argument("--samples", type=int, default=0, help="0 runs until Ctrl+C")
    capture = sub.add_parser("capture", help="bounded metadata-only capture on one selected interface")
    capture.add_argument("--interface", required=True)
    capture.add_argument("--duration", type=float, default=10)
    args = parser.parse_args(argv)
    try:
        if args.command == "interfaces":
            for interface in list_interfaces():
                emit(asdict(interface))
            return 0
        if args.command == "capture-interfaces":
            for interface in capture_interfaces():
                emit(interface)
            return 0
        if args.command == "capture":
            run_capture(args.interface, args.duration, emit)
            return 0
        if args.samples < 0:
            raise ValueError("samples must be nonnegative")
        selected = select_interface(args.interface)
        previous = read_counters(args.interface)
        tick, wall = time.monotonic(), time.time()
        session = str(uuid4())
        count = 0
        while args.samples == 0 or count < args.samples:
            time.sleep(max(0, tick + 1 - time.monotonic()))
            current_interface = select_interface(args.interface)
            current = read_counters(args.interface)
            now, utc = time.monotonic(), time.time()
            rates = calculate_rates(previous, current, now - tick)
            if current_interface != selected or abs((utc - wall) - (now - tick)) > 1:
                rates.update(valid=False, reason="interface_or_clock_change", delta=None,
                             upload_bytes_per_second=None, download_bytes_per_second=None)
            if not rates["valid"]:
                session = str(uuid4())
            emit({"schema_version": "phase1a-counters-v1", "mode": "LIVE",
                  "session_id": session, "interface": args.interface,
                  "observed_at": datetime.fromtimestamp(utc, timezone.utc).isoformat(),
                  "measurement_source": "OS_COUNTERS", "capture_capability": "OS_COUNTERS_ONLY",
                  "totals": asdict(current), **rates})
            previous, tick, wall, selected = current, now, utc, current_interface
            count += 1
        return 0
    except KeyboardInterrupt:
        print("Stopped by operator; no packet data retained.", file=sys.stderr)
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Sensor error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
