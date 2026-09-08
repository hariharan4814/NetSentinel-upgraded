"""Explicit opt-in validation: one public HTTP HEAD and one DNS query, no scanning.

Run from repository root using .venv Python and --interface <actual alias>.
Outputs only controlled flow summaries, operational counts and socket metadata.
"""
import argparse
import json
from pathlib import Path
import socket
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sensor.capture import run_capture, local_addresses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True)
    args = parser.parse_args()
    local = next((a for a in local_addresses(args.interface) if ":" not in a), None)
    if local is None:
        raise SystemExit("This controlled validation requires selected-interface IPv4")
    ready = threading.Event()
    results = {}
    records = []
    totals = {"windows": 0, "packets": 0, "ip_bytes": 0}

    def traffic():
        if not ready.wait(5):
            results["error"] = "capture did not become ready"
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(4)
                sock.bind((local, 0))
                results["tcp_local"] = sock.getsockname()
                sock.connect(("1.1.1.1", 80))
                sock.sendall(b"HEAD / HTTP/1.1\r\nHost: one.one.one.one\r\nConnection: close\r\n\r\n")
                results["tcp_response_received"] = sock.recv(4096).startswith(b"HTTP/")
        except OSError as exc:
            results["tcp_error"] = type(exc).__name__
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(4)
                sock.bind((local, 0))
                results["udp_local"] = sock.getsockname()
                # Standard recursive IN A query for example.com; one datagram.
                query = bytes.fromhex("4e5301000001000000000000") + b"\x07example\x03com\x00\x00\x01\x00\x01"
                sock.sendto(query, ("1.1.1.1", 53))
                reply, peer = sock.recvfrom(4096)
                results["dns_reply_valid"] = (peer == ("1.1.1.1", 53) and reply[:2] == query[:2]
                                              and len(reply) >= 12 and bool(reply[2] & 128)
                                              and reply[3] & 15 == 0)
                results["dns_request_bytes"] = len(query)
                results["dns_response_bytes"] = len(reply)
        except OSError as exc:
            results["udp_error"] = type(exc).__name__

    def emit(record):
        if record["type"] == "capture_started":
            records.append(record)
            ready.set()
        elif record["type"] == "window":
            totals["windows"] += 1
            totals["packets"] += sum(flow["packets"] for flow in record["flows"])
            totals["ip_bytes"] += sum(flow["ip_bytes"] for flow in record["flows"])
            matching = []
            for flow in record["flows"]:
                local_endpoint = results.get("tcp_local" if flow["protocol"] == "TCP" else "udp_local")
                port = 80 if flow["protocol"] == "TCP" else 53
                endpoints = {tuple(flow["endpoint_a"]), tuple(flow["endpoint_b"])}
                if local_endpoint and endpoints == {tuple(local_endpoint), ("1.1.1.1", port)}:
                    matching.append(flow)
            records.append({**record, "flows": matching,
                            "flow_filter": "controlled_endpoints_only",
                            "omitted_flow_count": len(record["flows"]) - len(matching),
                            "total_window_packets": sum(f["packets"] for f in record["flows"])})
        else:
            records.append(record)

    worker = threading.Thread(target=traffic, daemon=True)
    worker.start()
    started = time.monotonic()
    run_capture(args.interface, 24, emit)
    worker.join(timeout=1)
    flows = [flow for record in records if record["type"] == "window" for flow in record["flows"]]
    verified = all(any(f["protocol"] == protocol and f["outbound_packets"] > 0 and
                       f["inbound_packets"] > 0 for f in flows) for protocol in ("TCP", "UDP"))
    verified &= results.get("tcp_response_received", False) and results.get("dns_reply_valid", False)
    stopped = records[-1]
    verified &= (totals["packets"] == stopped["normalized"] and not stopped["queue_dropped"]
                 and not stopped["parse_errors"] and not stopped["late"]
                 and not stopped["flow_overflow"] and not stopped["shutdown_error"])
    udp = [f for f in flows if f["protocol"] == "UDP"]
    verified &= (sum(f["outbound_packets"] for f in udp) == 1 and
                 sum(f["inbound_packets"] for f in udp) == 1 and
                 sum(f["outbound_bytes"] for f in udp) == results.get("dns_request_bytes", 0) + 28 and
                 sum(f["inbound_bytes"] for f in udp) == results.get("dns_response_bytes", 0) + 28)
    print(json.dumps({"duration_wall_seconds": time.monotonic() - started,
                      "controlled_both_directions_verified": verified, "traffic": results,
                      "all_flow_totals": totals, "records": records}, indent=2))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
