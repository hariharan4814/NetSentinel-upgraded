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
from .interfaces import InterfaceUnavailable, select_interface
from .counters import read_counters, calculate_rates
from .features import host_features


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
        raise InterfaceUnavailable("Capture requires a non-loopback interface with IP addresses")
    # Winsock's if_nametoindex expects an internal name on Windows, not alias.
    luid, index_value = ctypes.c_ulonglong(), ctypes.c_ulong()
    api = ctypes.windll.iphlpapi
    if api.ConvertInterfaceAliasToLuid(ctypes.c_wchar_p(name), ctypes.byref(luid)) or api.ConvertInterfaceLuidToIndex(ctypes.byref(luid), ctypes.byref(index_value)):
        raise InterfaceUnavailable("Windows could not resolve the interface alias to an index")
    index = index_value.value
    conf.ifaces.reload()
    matches = [i for i in conf.ifaces.values() if i.index == index and i.name == name]
    if not matches:
        raise InterfaceUnavailable("Selected interface has no Npcap mapping available")
    if len(matches) != 1 or not matches[0].network_name.startswith("\\Device\\NPF_{"):
        raise ValueError("No unique Windows-index to Npcap mapping; run capture-interfaces")
    return selected, matches[0], addresses


def window_record(window, addresses=None):
    return {"type": "window", "schema_version": "phase1b-flow-v1", "mode": window.mode,
            "session_id": window.session_id, "interface": window.interface,
            "measurement_source": "PACKET_METADATA", "start": window.start,
            "end": window.start + 10, "finalized_at": window.finalized_at,
            "processed_at": time.time(), "partial": window.partial, "dropped": window.dropped,
            "kernel_loss": "unknown", "feature_schema_version": "host-v1",
            "features": host_features(window, addresses) if addresses is not None else None,
            "local_addresses": sorted(addresses) if addresses is not None else None,
            "flows": [
                {"protocol": key[1], "endpoint_a": key[2], "endpoint_b": key[3], **asdict(flow)}
                for key, flow in window.flows.items()]}


def stop_sniffer(sniffer):
    """Bounded join, including idle capture; never wait for the next packet."""
    if sniffer.running:
        sniffer.stop(join=False)
    sniffer.join(timeout=2)
    if sniffer.thread and sniffer.thread.is_alive():
        raise RuntimeError("Capture worker did not stop within two seconds")


def run_capture(interface, duration, emit, *, stop_event=None,
                recovery_retry_seconds=2, recovery_timeout_seconds=30,
                lifecycle_diagnostics=False):
    """Bounded supervisor; every recovered capture owns a new session/queue."""
    if not math.isfinite(duration) or not 0 < duration <= 1800:
        raise ValueError("duration must be finite and within (0, 1800] seconds")
    if not math.isfinite(recovery_retry_seconds) or not 0.1 <= recovery_retry_seconds <= 60:
        raise ValueError("recovery retry must be finite and within [0.1, 60] seconds")
    if not math.isfinite(recovery_timeout_seconds) or not 0 <= recovery_timeout_seconds <= 300:
        raise ValueError("recovery timeout must be finite and within [0, 300] seconds")
    origin = time.monotonic()
    deadline = origin + duration
    run_id = str(uuid4())
    identity = session = None
    latest = {}
    totals = {}
    losses = attempts = 0
    lost_at = lost_mono = None
    gap_seconds = 0.0
    last_diagnostic = None
    reason = "duration"
    sum_keys = ("normalized", "non_ip", "parse_errors", "flow_errors", "queue_dropped",
                "queue_remaining", "late", "flow_overflow")
    max_keys = ("queue_high_water", "flow_high_water", "window_high_water", "peak_rss_bytes")

    def status(state, **details):
        emit({"type": "capture_status", "mode": "LIVE", "run_id": run_id,
              "session_id": session, "interface": interface, "state": state,
              "observed_at": time.time(), "run_elapsed_seconds": time.monotonic() - origin,
              "loss_started_at": lost_at, "valid": state == "RUNNING", **details})

    def forward(record):
        nonlocal identity, session, lost_at, lost_mono, gap_seconds, losses, last_diagnostic, origin, deadline
        if record["type"] == "interface_loss":
            if lost_mono is None:
                losses += 1
                lost_mono, lost_at = time.monotonic(), record["observed_at"]
                last_diagnostic = {k: record[k] for k in ("exception_type", "exception_message")}
                status("INTERFACE_LOST", reason="interface_unavailable", **last_diagnostic)
            return
        if record["type"] == "capture_stopped":
            latest.update(record)
            for key in sum_keys:
                totals[key] = totals.get(key, 0) + record[key]
            for key in max_keys:
                totals[key] = max(totals.get(key, 0), record[key])
            return
        if record["type"] == "capture_started":
            session = record["session_id"]
            if identity is None:
                identity = record["capture_interface"]
                origin = time.monotonic()
                deadline = origin + duration
                emit({**record, "run_id": run_id})
                status("RUNNING", reason="started")
            else:
                gap = time.monotonic() - lost_mono
                gap_seconds += gap
                emit({**record, "type": "capture_restarted", "run_id": run_id})
                status("RUNNING", reason="interface_recovered", gap_seconds=gap,
                       gap_ended_at=time.time(), recovery_attempts=attempts)
                lost_at = lost_mono = None
            return
        emit({**record, "run_id": run_id})

    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                reason = "requested"
                break
            if time.monotonic() >= deadline:
                reason = "interface_unavailable" if lost_mono is not None else "duration"
                break
            try:
                _run_capture(interface, duration if identity is None else deadline - time.monotonic(), forward,
                             stop_event=stop_event, expected_identity=identity,
                             lifecycle_diagnostics=lifecycle_diagnostics,
                             start_deadline=min(deadline, lost_mono + recovery_timeout_seconds)
                             if lost_mono is not None else None)
                reason = latest.get("reason", "duration")
                break
            except InterfaceUnavailable as exc:
                last_diagnostic = {"exception_type": type(exc).__name__, "exception_message": str(exc)}
                if lost_mono is None:
                    losses += 1
                    lost_mono, lost_at = time.monotonic(), time.time()
                    status("INTERFACE_LOST", reason="interface_unavailable", **last_diagnostic)
                # Initial absence has no trusted GUID to recover against.
                recovery_deadline = min(deadline, lost_mono + recovery_timeout_seconds)
                if identity is None or time.monotonic() >= recovery_deadline:
                    reason = "interface_unavailable"
                    break
                status("RECOVERING", reason="waiting_for_same_interface",
                       retry_seconds=recovery_retry_seconds, recovery_attempts=attempts)
                delay = min(recovery_retry_seconds, recovery_deadline - time.monotonic())
                if stop_event is not None:
                    stop_event.wait(max(0, delay))
                else:
                    time.sleep(max(0, delay))
                if stop_event is not None and stop_event.is_set():
                    reason = "requested"
                    break
                if time.monotonic() >= recovery_deadline:
                    reason = "interface_unavailable"
                    break
                attempts += 1
    except KeyboardInterrupt:
        reason = "operator"
    except Exception:
        reason = "error"
        raise
    finally:
        if lost_mono is not None:
            gap_seconds += time.monotonic() - lost_mono
        status("STOPPED", reason=reason, interface_losses=losses,
               monitoring_gap_seconds=gap_seconds, diagnostic=last_diagnostic)
        if latest:
            emit({**latest, **totals, "run_id": run_id, "reason": reason,
                  "interface_losses": losses, "recovery_attempts": attempts,
                  "monitoring_gap_seconds": gap_seconds, "diagnostic": last_diagnostic})
    return reason


def _run_capture(interface, duration, emit, *, stop_event=None, expected_identity=None,
                 start_deadline=None, lifecycle_diagnostics=False):
    if not math.isfinite(duration) or not 0 < duration <= 1800:
        raise ValueError("duration must be finite and within (0, 1800] seconds")
    conf = capture_preflight()
    selected, device, addresses = resolve_capture_interface(interface, conf)
    if expected_identity is not None and device.network_name != expected_identity:
        raise RuntimeError("Interface identity changed; refusing capture on a replacement GUID")
    from scapy.all import AsyncSniffer
    from .normalize import packet_to_metadata

    queue = MetadataQueue()
    counts = {"normalized": 0, "non_ip": 0, "parse_errors": 0, "flow_errors": 0}
    process = psutil.Process()
    process.cpu_percent()
    peak_rss = flow_high_water = window_high_water = 0
    ready = threading.Event()
    session = str(uuid4())
    agg = None
    capture_socket = sniffer = None
    stopped_by = "duration"

    def lifecycle(step):
        if lifecycle_diagnostics:
            emit({"type": "capture_lifecycle", "session_id": session, "mode": "LIVE",
                  "observed_at": time.time(), "step": step,
                  "worker_running": bool(sniffer and sniffer.running),
                  "worker_alive": bool(sniffer and sniffer.thread and sniffer.thread.is_alive())})

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
        nonlocal flow_high_water, window_high_water
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
            try:
                windows = agg.advance(max(agg.watermark, metadata.timestamp))
                agg.add(metadata)
                flow_high_water = max(flow_high_water, sum(len(w.flows) for w in agg.windows.values()))
                window_high_water = max(window_high_water, len(agg.windows))
            except (ValueError, TypeError):
                counts["flow_errors"] += 1
                agg.mark_loss()
                raise
            for window in windows:
                emit(window_record(window, addresses))

    try:
        if start_deadline is not None and time.monotonic() >= start_deadline:
            raise InterfaceUnavailable("Recovery deadline expired before capture restart")
        # No promiscuous/monitor mode, packet storage, disk capture or reassembly.
        lifecycle("socket_open_begin")
        capture_socket = conf.L2listen(iface=device, promisc=False, filter="ip or ip6")
        lifecycle("socket_open_end")
        started = time.time()
        agg = WindowAggregator(start=started, mode="LIVE", session_id=session,
                               interface=device.network_name)
        sniffer = AsyncSniffer(opened_socket=capture_socket, store=False, prn=receive,
                               started_callback=ready.set)
        lifecycle("worker_start_begin")
        sniffer.start()
        if not ready.wait(2):
            raise RuntimeError("Capture worker failed to start; check Npcap permissions")
        lifecycle("worker_ready")
        if start_deadline is not None and time.monotonic() >= start_deadline:
            raise InterfaceUnavailable("Recovery deadline expired during capture restart")
        previous_counters = read_counters(interface)
        emit({"type": "capture_started", "mode": "LIVE", "session_id": session,
              "interface": interface, "capture_interface": device.network_name,
              "interface_index": device.index, "observed_at": started,
              "duration_seconds": duration, "filter": "ip or ip6", "promiscuous": False,
              "kernel_loss": "unknown", "schema_version": "phase1b-capture-v1"})
        origin_mono, origin_wall = time.monotonic(), time.time()
        last_check = time.monotonic()
        next_check = origin_mono + 1
        while time.monotonic() - origin_mono < duration:
            if stop_event is not None and stop_event.is_set():
                stopped_by = "requested"
                break
            if not sniffer.running:
                select_interface(interface)  # A known link loss can be recovered; other worker failures cannot.
                raise RuntimeError("Capture stopped unexpectedly; check interface/driver")
            now_mono, now_wall = time.monotonic(), time.time()
            if abs((now_wall - origin_wall) - (now_mono - origin_mono)) > 1:
                raise RuntimeError("Clock discontinuity; restart capture as a new session")
            if now_mono >= next_check:
                if select_interface(interface) != selected or local_addresses(interface) != addresses:
                    raise InterfaceUnavailable("Interface/address context changed; new capture session required")
                current = read_counters(interface)
                sample_mono = time.monotonic()
                sample_end = time.time()
                rates = calculate_rates(previous_counters, current, sample_mono - last_check)
                memory = process.memory_info()
                rss = memory.rss
                peak_rss = max(peak_rss, rss, getattr(memory, "peak_wset", 0))
                emit({"type": "health", "mode": "LIVE", "session_id": session,
                      "interface": interface, "observed_at": sample_end,
                      "capture_state": "running", "measurement_source": "OS_COUNTERS",
                      "totals": asdict(current), **rates, "rss_bytes": rss,
                      "peak_rss_bytes": peak_rss, "cpu_percent": process.cpu_percent(),
                      "queue_size": len(queue), "queue_high_water": queue.high_water,
                      "flow_entries": sum(len(w.flows) for w in agg.windows.values()),
                      "flow_high_water": flow_high_water, "open_windows": len(agg.windows),
                      "window_high_water": window_high_water, **counts,
                      "queue_dropped": queue.dropped, "flow_overflow": agg.overflow,
                      "late": agg.late, "kernel_loss": "unknown"})
                previous_counters, last_check = current, sample_mono
                # Anchor cadence to the session, not completion of slow OS calls.
                # Skip missed deadlines; never fabricate catch-up counter records.
                next_check = origin_mono + math.floor(sample_mono - origin_mono) + 1
            drain()
            for window in agg.advance(max(agg.watermark, now_wall)):
                emit(window_record(window, addresses))
            flow_high_water = max(flow_high_water, sum(len(w.flows) for w in agg.windows.values()))
            window_high_water = max(window_high_water, len(agg.windows))
            time.sleep(0.05)
    except InterfaceUnavailable as exc:
        stopped_by = "interface_lost"
        if agg:
            agg.mark_loss()
        emit({"type": "interface_loss", "observed_at": time.time(),
              "exception_type": type(exc).__name__, "exception_message": str(exc)})
        raise
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
        shutdown_started = time.monotonic()
        shutdown_error = False
        try:
            if sniffer:
                lifecycle("worker_stop_join_begin")
                stop_sniffer(sniffer)
                lifecycle("worker_stop_join_end")
        except Exception:
            shutdown_error = True
            lifecycle("worker_stop_join_failed")
            if agg:
                agg.mark_loss()
        finally:
            if capture_socket:
                lifecycle("socket_close_begin")
                capture_socket.close()
                lifecycle("socket_close_end")
        if agg:
            if stopped_by != "error" and not shutdown_error:
                try:
                    drain()
                except Exception:
                    shutdown_error = True
                    agg.mark_loss()
            else:
                agg.mark_loss()
            for window in agg.flush():
                emit(window_record(window, addresses))
            emit({"type": "capture_stopped", "mode": "LIVE", "session_id": session,
                  "interface": device.network_name, "reason": stopped_by,
                  **counts, "queue_dropped": queue.dropped, "queue_remaining": len(queue),
                  "late": agg.late, "flow_overflow": agg.overflow,
                  "queue_high_water": queue.high_water, "flow_high_water": flow_high_water,
                  "window_high_water": window_high_water,
                  "final_rss_bytes": process.memory_info().rss,
                  "peak_rss_bytes": max(peak_rss, process.memory_info().rss,
                                        getattr(process.memory_info(), "peak_wset", 0)),
                  "shutdown_seconds": time.monotonic() - shutdown_started,
                  "shutdown_error": shutdown_error, "kernel_loss": "unknown"})
        if shutdown_error:
            raise RuntimeError("Capture shutdown failed; restart the process before further capture")
