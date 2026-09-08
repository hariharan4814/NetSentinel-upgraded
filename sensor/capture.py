"""Npcap source, bounded metadata queue, and independent local flow runner."""
from dataclasses import asdict
import ctypes
from ipaddress import ip_address
import math
import os
from pathlib import Path
import socket
import threading
import time
from uuid import uuid4

import psutil

from .flows import MetadataQueue, WindowAggregator
from .interfaces import select_interface


def capture_preflight():
    if os.name != "nt":
        raise RuntimeError("Only the inspected Windows/Npcap path is supported")
    root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    if not (root / "System32/Npcap/wpcap.dll").is_file():
        raise RuntimeError("Npcap not detected in the standard path. Install Npcap manually "
                           "before packet testing; no capture was attempted. Counters remain available.")
    check_driver_access()
    try:
        from scapy.all import conf
        from scapy.libs.winpcapy import pcap_lib_version
    except ImportError:
        raise RuntimeError("Install requirements-sensor.txt in the project .venv") from None
    if not conf.use_pcap or b"Npcap" not in pcap_lib_version():
        raise RuntimeError("Npcap is not the active capture provider; check driver setup")
    return conf


def check_driver_access():
    """Prevent NpcapHelper from implicitly requesting elevation on socket open."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Services\npcap\Parameters") as key:
            admin_only, _ = winreg.QueryValueEx(key, "AdminOnly")
    except OSError:
        raise RuntimeError("Cannot verify Npcap access options; inspect driver installation manually") from None
    if admin_only and not ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError("Npcap restricts capture to administrators. Start an elevated sensor "
                           "manually if authorized; automatic elevation is disabled")


def local_addresses(name):
    return {str(ip_address(a.address.split("%")[0]))
            for a in psutil.net_if_addrs().get(name, [])
            if a.family in {socket.AF_INET, socket.AF_INET6}}


def capture_interfaces():
    conf = capture_preflight()
    conf.ifaces.reload()
    return [{"name": i.name, "index": i.index, "guid": getattr(i, "guid", None),
             "capture_interface": i.network_name} for i in conf.ifaces.values()]


def resolve_capture_interface(name, conf):
    selected = select_interface(name)
    addresses = local_addresses(name)
    if not addresses or all(ip_address(a).is_loopback for a in addresses):
        raise ValueError("Capture requires a non-loopback interface with IP addresses")
    # Winsock's if_nametoindex expects an internal name on Windows, not alias.
    luid, index_value = ctypes.c_ulonglong(), ctypes.c_ulong()
    api = ctypes.windll.iphlpapi
    if api.ConvertInterfaceAliasToLuid(ctypes.c_wchar_p(name), ctypes.byref(luid)) or api.ConvertInterfaceLuidToIndex(ctypes.byref(luid), ctypes.byref(index_value)):
        raise ValueError("Windows could not resolve the interface alias to an index")
    index = index_value.value
    conf.ifaces.reload()
    matches = [i for i in conf.ifaces.values() if i.index == index and i.name == name]
    if len(matches) != 1 or not matches[0].network_name.startswith("\\Device\\NPF_{"):
        raise ValueError("No unique Windows-index to Npcap mapping; run capture-interfaces")
    return selected, matches[0], addresses


def window_record(window):
    return {"type": "window", "schema_version": "phase1b-flow-v1", "mode": window.mode,
            "session_id": window.session_id, "interface": window.interface,
            "measurement_source": "PACKET_METADATA", "start": window.start,
            "end": window.start + 10, "finalized_at": window.finalized_at,
            "processed_at": time.time(), "partial": window.partial, "dropped": window.dropped,
            "kernel_loss": "unknown", "flows": [
                {"protocol": key[1], "endpoint_a": key[2], "endpoint_b": key[3], **asdict(flow)}
                for key, flow in window.flows.items()]}


def stop_sniffer(sniffer):
    """Bounded join, including idle capture; never wait for the next packet."""
    if sniffer.running:
        sniffer.stop(join=False)
    sniffer.join(timeout=2)
    if sniffer.thread and sniffer.thread.is_alive():
        raise RuntimeError("Capture worker did not stop within two seconds")


def run_capture(interface, duration, emit):
    if not math.isfinite(duration) or not 0 < duration <= 1800:
        raise ValueError("duration must be finite and within (0, 1800] seconds")
    conf = capture_preflight()
    selected, device, addresses = resolve_capture_interface(interface, conf)
    from scapy.all import AsyncSniffer
    from .normalize import packet_to_metadata

    queue = MetadataQueue()
    counts = {"normalized": 0, "non_ip": 0, "parse_errors": 0}
    ready = threading.Event()
    session = str(uuid4())
    agg = None
    capture_socket = sniffer = None
    stopped_by = "duration"

    def receive(packet):
        try:
            metadata = packet_to_metadata(packet, device.network_name, addresses)
            if metadata is None:
                counts["non_ip"] += 1
            else:
                queue.put(metadata)
                counts["normalized"] += 1
        except Exception:
            # Never log packet/exception repr: parsers may include captured bytes.
            counts["parse_errors"] += 1

    def drain():
        if queue.dropped or counts["parse_errors"]:
            agg.mark_loss()
        for _ in range(len(queue)):
            metadata = queue.pop()
            if metadata is None:
                break
            if metadata.timestamp > time.time() + 1:
                agg.mark_loss()
                counts["parse_errors"] += 1
                continue
            for window in agg.advance(max(agg.watermark, metadata.timestamp)):
                emit(window_record(window))
            agg.add(metadata)

    try:
        # No promiscuous/monitor mode, packet storage, disk capture or reassembly.
        capture_socket = conf.L2listen(iface=device, promisc=False, filter="ip or ip6")
        started = time.time()
        agg = WindowAggregator(start=started, mode="LIVE", session_id=session,
                               interface=device.network_name)
        sniffer = AsyncSniffer(opened_socket=capture_socket, store=False, prn=receive,
                               started_callback=ready.set)
        sniffer.start()
        if not ready.wait(2):
            raise RuntimeError("Capture worker failed to start; check Npcap permissions")
        emit({"type": "capture_started", "mode": "LIVE", "session_id": session,
              "interface": interface, "capture_interface": device.network_name,
              "interface_index": device.index, "observed_at": started,
              "duration_seconds": duration, "filter": "ip or ip6", "promiscuous": False,
              "kernel_loss": "unknown", "schema_version": "phase1b-capture-v1"})
        origin_mono, origin_wall = time.monotonic(), time.time()
        last_check = origin_mono
        while time.monotonic() - origin_mono < duration:
            if not sniffer.running:
                raise RuntimeError("Capture stopped unexpectedly; check interface/driver")
            now_mono, now_wall = time.monotonic(), time.time()
            if abs((now_wall - origin_wall) - (now_mono - origin_mono)) > 1:
                raise RuntimeError("Clock discontinuity; restart capture as a new session")
            if now_mono - last_check >= 1:
                if select_interface(interface) != selected or local_addresses(interface) != addresses:
                    raise RuntimeError("Interface/address change; restart capture as a new session")
                last_check = now_mono
            drain()
            for window in agg.advance(max(agg.watermark, now_wall)):
                emit(window_record(window))
            time.sleep(0.05)
    except KeyboardInterrupt:
        stopped_by = "operator"
    except Exception as exc:
        stopped_by = "error"
        if agg:
            agg.mark_loss()
        if isinstance(exc, (ValueError, RuntimeError)):
            raise
        raise RuntimeError("Capture failed: check Npcap service, interface and capture permissions; "
                           "no automatic elevation or configuration change was attempted") from None
    finally:
        shutdown_error = False
        try:
            if sniffer:
                stop_sniffer(sniffer)
        except Exception:
            shutdown_error = True
            if agg:
                agg.mark_loss()
        finally:
            if capture_socket:
                capture_socket.close()
        if agg:
            if stopped_by != "error" and not shutdown_error:
                drain()
            else:
                agg.mark_loss()
            for window in agg.flush():
                emit(window_record(window))
            emit({"type": "capture_stopped", "mode": "LIVE", "session_id": session,
                  "interface": device.network_name, "reason": stopped_by,
                  **counts, "queue_dropped": queue.dropped, "queue_remaining": len(queue),
                  "late": agg.late, "flow_overflow": agg.overflow,
                  "shutdown_error": shutdown_error, "kernel_loss": "unknown"})
        if shutdown_error:
            raise RuntimeError("Capture shutdown failed; restart the process before further capture")
