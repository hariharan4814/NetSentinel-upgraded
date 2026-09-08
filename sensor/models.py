"""Whitelisted metadata only. No packet objects or payload fields."""
from dataclasses import dataclass
from ipaddress import ip_address
from math import isfinite


@dataclass(frozen=True, slots=True)
class PacketMetadata:
    timestamp: float  # UTC Unix seconds
    interface: str
    source_ip: str
    destination_ip: str
    source_port: int | None
    destination_port: int | None
    protocol: str
    packet_length: int  # observed IP bytes, not wire or payload bytes
    direction: str = "unknown"
    incomplete: bool = False
    tcp_syn: bool | None = None

    def __post_init__(self):
        if not isfinite(self.timestamp) or self.timestamp < 0:
            raise ValueError("timestamp must be finite UTC epoch seconds")
        for field in ("source_ip", "destination_ip"):
            object.__setattr__(self, field, str(ip_address(getattr(self, field))))
        if not self.interface or len(self.interface) > 256:
            raise ValueError("invalid interface")
        if self.protocol not in {"TCP", "UDP", "ICMP", "ICMPV6", "OTHER"}:
            raise ValueError("invalid protocol")
        if self.direction not in {"inbound", "outbound", "unknown"}:
            raise ValueError("invalid direction")
        if not 0 <= self.packet_length <= 2**32 - 1:
            raise ValueError("invalid IP length")
        for port in (self.source_port, self.destination_port):
            if port is not None and not 0 <= port <= 65535:
                raise ValueError("invalid port")


def infer_direction(source: str, destination: str, local_ips: set[str]) -> str:
    """Only use selected-interface addresses; both/neither local is unknown."""
    local = {ip_address(address) for address in local_ips}
    src, dst = ip_address(source) in local, ip_address(destination) in local
    return "outbound" if src and not dst else "inbound" if dst and not src else "unknown"
