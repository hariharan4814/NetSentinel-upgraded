"""Pure bounded, session-scoped ten-second aggregation; never retains packets."""
from collections import deque
from dataclasses import dataclass, field
from math import floor, isfinite
from threading import Lock

from .models import PacketMetadata


def flow_key(packet: PacketMetadata) -> tuple:
    endpoints = [(packet.source_ip, packet.source_port),
                 (packet.destination_ip, packet.destination_port)]
    endpoints.sort(key=lambda endpoint: (endpoint[0], -1 if endpoint[1] is None else endpoint[1]))
    return (packet.interface, packet.protocol, *endpoints)


class MetadataQueue:
    """Drop oldest under pressure; consumer must mark affected windows partial."""
    def __init__(self, capacity=20_000):
        if not 1 <= capacity <= 20_000:
            raise ValueError("queue capacity must be 1..20000")
        self._items = deque(maxlen=capacity)
        self._lock = Lock()
        self.dropped = 0
        self.high_water = 0

    def put(self, packet: PacketMetadata):
        if not isinstance(packet, PacketMetadata):
            raise TypeError("only PacketMetadata is accepted")
        with self._lock:
            if len(self._items) == self._items.maxlen:
                self.dropped += 1
            self._items.append(packet)
            self.high_water = max(self.high_water, len(self._items))

    def pop(self):
        with self._lock:
            return self._items.popleft() if self._items else None

    def __len__(self):
        with self._lock:
            return len(self._items)


@dataclass(slots=True)
class Flow:
    packets: int = 0
    ip_bytes: int = 0
    outbound_packets: int = 0
    outbound_bytes: int = 0
    inbound_packets: int = 0
    inbound_bytes: int = 0
    unknown_packets: int = 0
    tcp_syn_packets: int = 0
    incomplete: bool = False
    first_observed: float | None = None
    last_observed: float | None = None
    min_ip_bytes: int | None = None
    max_ip_bytes: int = 0


@dataclass(slots=True)
class Window:
    start: int
    mode: str
    session_id: str
    interface: str
    flows: dict = field(default_factory=dict)
    partial: bool = False
    dropped: int = 0
    finalized_at: float | None = None
    schema_version: str = "phase1a-flow-v1"


class WindowAggregator:
    """Caller supplies a monotonic event-time watermark, including idle ticks.

    At most two open windows and 10000 total flow entries. Large clock gaps
    require a new session instead of allocating an unbounded idle history.
    """
    def __init__(self, *, start: float, mode: str, session_id: str,
                 interface: str, max_flows=10_000):
        if mode not in {"LIVE", "SIMULATION", "REPLAY"} or not session_id or not interface:
            raise ValueError("explicit provenance required")
        if not isfinite(start) or start < 0 or not 1 <= max_flows <= 10_000:
            raise ValueError("invalid start/capacity")
        self.mode, self.session_id, self.interface = mode, session_id, interface
        self.max_flows, self.watermark, self.started = max_flows, start, start
        self.windows = {}
        self.next_start = floor(start / 10) * 10
        self.late = self.overflow = 0
        self.closed = False
        self.coverage_loss = False

    def _window(self, start):
        if start not in self.windows:
            self.windows[start] = Window(start, self.mode, self.session_id, self.interface,
                                         partial=start < self.started or self.coverage_loss)
        return self.windows[start]

    def advance(self, now: float) -> list[Window]:
        if self.closed:
            raise ValueError("session closed")
        if not isfinite(now) or now < self.watermark or now - self.watermark > 30:
            raise ValueError("clock discontinuity: flush partial and start a new session")
        self.watermark = now
        result = []
        while self.next_start + 12 <= now:
            window = self._window(self.next_start)
            window.finalized_at = now
            result.append(self.windows.pop(self.next_start))
            self.next_start += 10
        return result

    def add(self, packet: PacketMetadata) -> bool:
        if self.closed or packet.interface != self.interface:
            raise ValueError("closed session or interface mismatch")
        if packet.timestamp > self.watermark:
            raise ValueError("advance watermark before adding future metadata")
        start = floor(packet.timestamp / 10) * 10
        if packet.timestamp < self.started or start < self.next_start:
            self.late += 1
            self.mark_loss()
            return False
        window = self._window(start)
        key = flow_key(packet)
        if key not in window.flows:
            if sum(len(w.flows) for w in self.windows.values()) >= self.max_flows:
                self.overflow += 1
                window.dropped += 1
                window.partial = True
                return False
            window.flows[key] = Flow()
        flow = window.flows[key]
        flow.packets += 1
        flow.ip_bytes += packet.packet_length
        flow.first_observed = min(flow.first_observed, packet.timestamp) if flow.first_observed is not None else packet.timestamp
        flow.last_observed = max(flow.last_observed, packet.timestamp) if flow.last_observed is not None else packet.timestamp
        flow.min_ip_bytes = min(flow.min_ip_bytes, packet.packet_length) if flow.min_ip_bytes is not None else packet.packet_length
        flow.max_ip_bytes = max(flow.max_ip_bytes, packet.packet_length)
        if packet.direction == "unknown":
            flow.unknown_packets += 1
        else:
            name = packet.direction
            setattr(flow, name + "_packets", getattr(flow, name + "_packets") + 1)
            setattr(flow, name + "_bytes", getattr(flow, name + "_bytes") + packet.packet_length)
        flow.tcp_syn_packets += int(packet.protocol == "TCP" and packet.tcp_syn is True)
        flow.incomplete |= (packet.incomplete or packet.direction == "unknown" or
                            (packet.protocol in {"TCP", "UDP"} and
                             (packet.source_port is None or packet.destination_port is None)) or
                            (packet.protocol == "TCP" and packet.tcp_syn is None))
        window.partial |= flow.incomplete
        return True

    def mark_loss(self):
        """Conservatively invalidate remaining session after uncertain loss scope."""
        self.coverage_loss = True
        for window in self.windows.values():
            window.partial = True

    def flush(self) -> list[Window]:
        self.closed = True
        result = list(self.windows.values())
        for window in result:
            window.partial = True
            window.finalized_at = self.watermark
        self.windows.clear()
        return result
