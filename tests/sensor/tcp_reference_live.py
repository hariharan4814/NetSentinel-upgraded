"""Opt-in matched TCP reference, one laptop HTTP HEAD; metadata totals only.

Second Npcap socket shares the observation point, but uses independent Ethernet/
IPv4 struct parsing and no sensor normalizer/aggregator. This is not wire truth.
"""
import argparse
import json
from pathlib import Path
import socket
import struct
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sensor.capture import capture_preflight, resolve_capture_interface, run_capture, stop_sniffer


def reference_fields(frame):
    if len(frame) < 34 or frame[12:14] != b"\x08\x00":
        raise ValueError("requires Ethernet IPv4 without VLAN")
    version_ihl, _, length = struct.unpack_from("!BBH", frame, 14)
    ihl = (version_ihl & 15) * 4
    if version_ihl >> 4 != 4 or ihl < 20 or length < ihl + 20 or len(frame) < 14 + length or frame[23] != 6:
        raise ValueError("invalid or unsupported IPv4 TCP frame")
    if struct.unpack_from("!H", frame, 20)[0] & 0x3fff:
        raise ValueError("fragment unsupported")
    src, dst = socket.inet_ntoa(frame[26:30]), socket.inet_ntoa(frame[30:34])
    sport, dport = struct.unpack_from("!HH", frame, 14 + ihl)
    return src, dst, sport, dport, length


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True)
    args = parser.parse_args()
    conf = capture_preflight()
    _, device, addresses = resolve_capture_interface(args.interface, conf)
    local = next(a for a in addresses if ":" not in a)
    from scapy.all import AsyncSniffer
    reference = dict(packets=0, ip_bytes=0, outbound_packets=0, inbound_packets=0, outbound_bytes=0, inbound_bytes=0)
    captured = dict(reference)
    state = {"reference_errors": 0, "http_response": False}
    ready = threading.Event()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.bind((local, 0))
        port = client.getsockname()[1]
        def receive(packet):
            try:
                src, dst, sport, dport, length = reference_fields(bytes(packet))
                if (src, dst, sport, dport) == (local, "1.1.1.1", port, 80):
                    direction = "outbound"
                elif (src, dst, sport, dport) == ("1.1.1.1", local, 80, port):
                    direction = "inbound"
                else:
                    return
                reference["packets"] += 1
                reference["ip_bytes"] += length
                reference[direction + "_packets"] += 1
                reference[direction + "_bytes"] += length
            except Exception:
                state["reference_errors"] += 1
        def traffic():
            if not ready.wait(5):
                return
            try:
                client.connect(("1.1.1.1", 80))
                client.sendall(b"HEAD / HTTP/1.1\r\nHost: one.one.one.one\r\nConnection: close\r\n\r\n")
                state["http_response"] = client.recv(4096).startswith(b"HTTP/")
            except OSError as exc:
                state["traffic_error"] = type(exc).__name__
            finally:
                client.close()
        def emit(record):
            if record["type"] == "capture_started":
                ready.set()
            elif record["type"] == "window":
                for flow in record["flows"]:
                    if flow["protocol"] == "TCP" and {tuple(flow["endpoint_a"]), tuple(flow["endpoint_b"])} == {(local, port), ("1.1.1.1", 80)}:
                        for key in captured:
                            captured[key] += flow[key]
            elif record["type"] == "capture_stopped":
                state["sensor_stop"] = {k: v for k, v in record.items() if k != "interface"}
        ref_ready = threading.Event()
        ref_socket = conf.L2listen(iface=device, promisc=False, filter=f"tcp and host 1.1.1.1 and port 80 and port {port}")
        sniffer = AsyncSniffer(opened_socket=ref_socket, store=False, prn=receive, started_callback=ref_ready.set)
        worker = threading.Thread(target=traffic, daemon=True)
        try:
            sniffer.start()
            if not ref_ready.wait(2):
                raise RuntimeError("reference capture not ready")
            worker.start()
            run_capture(args.interface, 16, emit)
            worker.join(timeout=1)
        finally:
            try:
                stop_sniffer(sniffer)
            finally:
                ref_socket.close()
    discrepancy = {k: captured[k] - reference[k] for k in captured}
    percentages = {k: abs(discrepancy[k])/reference[k]*100 if reference[k] else None for k in captured}
    stop = state.get("sensor_stop", {})
    passed = (state["http_response"] and not state["reference_errors"] and
              all(v is not None and v <= 5 for v in percentages.values()) and
              bool(stop) and not stop.get("interface_losses", 0) and stop["reason"] == "duration"
              and not any(stop[k] for k in ("parse_errors", "flow_errors", "queue_dropped", "flow_overflow", "late", "shutdown_error")))
    print(json.dumps({"reference": reference, "captured": captured, "discrepancy": discrepancy,
                      "discrepancy_percent": percentages, "state": state, "passed": passed,
                      "reference_scope": "same Npcap interface; exact ephemeral TCP tuple; reference opened before connect, closed after sensor; one exchange only",
                      "limitations": "shared driver/offload blind spots; kernel loss unknown; compare discrepancies before acceptance"}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, StopIteration) as exc:
        print(json.dumps({"type": "reference_error", "error": type(exc).__name__,
                          "reason": "verify selected interface, IPv4 and Npcap; no matched result", "passed": False}))
        raise SystemExit(2)
