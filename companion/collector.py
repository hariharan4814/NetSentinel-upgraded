"""Explicit, bounded metadata-only capture using the existing sensor normalizer."""
import queue
import threading
import time

from .attribution import Snapshot, socket_snapshot, match_packet


class Collector:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None
        self.status = {"state": "stopped", "interface": None, "started_at": None,
                       "last_packet_at": None, "dropped_metadata": 0, "parse_failures": 0,
                       "socket_snapshot_complete": False, "error": None,
                       "method": "packet-socket-approx-v1", "kernel_loss": "unknown"}

    def view(self):
        with self.lock:
            return dict(self.status)

    def start(self, interface, consent):
        if consent is not True:
            raise ValueError("Explicit packet metadata observation consent is required")
        with self.lock:
            if self.thread and self.thread.is_alive():
                raise ValueError("Observation is already active")
            from sensor.capture import capture_preflight, resolve_capture_interface
            from sensor.normalize import packet_to_metadata
            from scapy.all import AsyncSniffer
            conf = capture_preflight()
            _, selected, addresses = resolve_capture_interface(interface, conf)
            self.stop_event.clear()
            self.status.update(state="starting", interface=interface, started_at=time.time(), error=None,
                               dropped_metadata=0, parse_failures=0, last_packet_at=None)
            metadata_queue = queue.Queue(maxsize=8192)

            def observe(packet):
                try:
                    metadata = packet_to_metadata(packet, interface, addresses)
                    if metadata:
                        metadata_queue.put_nowait(metadata)
                except queue.Full:
                    self.status["dropped_metadata"] += 1
                except (ValueError, TypeError, AttributeError):
                    self.status["parse_failures"] += 1

            sniffer = AsyncSniffer(iface=selected.network_name, store=False, prn=observe, filter="ip or ip6")

            def collect():
                snapshot = Snapshot(0, (), False)
                cached = {}
                try:
                    sniffer.start()
                    self.status["state"] = "observing"
                    while not self.stop_event.wait(.15):
                        if time.time()-snapshot.at >= .5:
                            import psutil
                            from sensor.capture import local_addresses
                            stats = psutil.net_if_stats().get(interface)
                            if not stats or not stats.isup or local_addresses(interface) != addresses:
                                raise RuntimeError("Selected interface changed; restart observation explicitly")
                            snapshot = socket_snapshot()
                            self.status["socket_snapshot_complete"] = snapshot.complete
                            for owner in snapshot.owners:
                                if owner.executable and owner.executable not in cached:
                                    cached[owner.executable] = self.store.discover(owner.executable)
                            if len(cached) > 512:
                                cached.clear()
                        batch = []
                        for _ in range(2048):
                            try:
                                packet = metadata_queue.get_nowait()
                            except queue.Empty:
                                break
                            path = match_packet(packet, snapshot)
                            batch.append((cached.get(path), packet))
                            self.status["last_packet_at"] = packet.timestamp
                        if batch:
                            self.store.record(batch)
                        if getattr(sniffer, "exception", None):
                            raise RuntimeError("Capture failed")
                    # Queued records after stop are dropped and explicitly counted.
                    self.status["dropped_metadata"] += metadata_queue.qsize()
                except Exception:
                    self.status.update(state="unavailable", error="Observation failed; check interface, Npcap and permissions. The missing interval is not zero traffic.")
                finally:
                    try:
                        if sniffer.running:
                            sniffer.stop(join=False)
                            sniffer.join(timeout=3)
                    except Exception:
                        self.status["error"] = "Capture stop could not be confirmed; close the companion process."
                    if self.status["state"] != "unavailable":
                        self.status["state"] = "stopped"
                    self.store.event("observation", "capture_stopped", "Packet observation stopped; missing intervals are not zero traffic.")

            self.thread = threading.Thread(target=collect, name="netsentinel-observation", daemon=True)
            self.thread.start()
        self.store.event("observation", "capture_started", "Operator enabled metadata observation on one selected interface.")

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                raise RuntimeError("Capture stop timed out; exit the companion")


def adapters():
    import psutil
    import socket
    result = []
    stats = psutil.net_if_stats()
    for name, addresses in list(psutil.net_if_addrs().items())[:64]:
        result.append({"name": name, "up": bool(stats.get(name) and stats[name].isup),
                       "addresses": [a.address for a in addresses if a.family in {socket.AF_INET, socket.AF_INET6}][:16]})
    return result
