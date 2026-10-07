"""Approximate IP-byte attribution, never socket-list or interface-byte accounting."""
from dataclasses import dataclass
from ipaddress import ip_address
import socket
import time

from .identity import canonical


@dataclass(frozen=True)
class SocketOwner:
    protocol: str
    local_ip: str
    local_port: int
    remote_ip: str | None
    remote_port: int | None
    executable: str | None
    pid: int | None = None


@dataclass(frozen=True)
class Snapshot:
    at: float
    owners: tuple[SocketOwner, ...]
    complete: bool = True


def match_packet(packet, snapshot, now=None):
    """Return a canonical executable only for a unique same-executable match.

    Unknown owners participate in ambiguity. Fragmented/unknown-direction traffic
    is unassigned. UDP wildcard listeners can match, but multiple owners cannot.
    Snapshot freshness is checked against observation AND processing time.
    """
    now = time.time() if now is None else now
    if (not snapshot.complete or abs(packet.timestamp - snapshot.at) > 2
            or now - snapshot.at > 2 or snapshot.at > now + .1
            or packet.incomplete or packet.direction not in {"outbound", "inbound"}
            or packet.protocol not in {"TCP", "UDP"}):
        return None
    if packet.direction == "outbound":
        local, port, remote, rport = packet.source_ip, packet.source_port, packet.destination_ip, packet.destination_port
    else:
        local, port, remote, rport = packet.destination_ip, packet.destination_port, packet.source_ip, packet.source_port
    candidates = set()
    for owner in snapshot.owners:
        if owner.protocol != packet.protocol or owner.local_port != port:
            continue
        wildcard = "::" if ip_address(local).version == 6 else "0.0.0.0"
        if owner.local_ip not in {local, wildcard}:
            continue
        if owner.remote_ip is not None and (owner.remote_ip, owner.remote_port) != (remote, rport):
            continue
        if owner.remote_ip is None and owner.protocol == "TCP":
            continue  # A listening TCP socket is not proof of the accepted owner.
        candidates.add(owner.executable)
    return next(iter(candidates)) if len(candidates) == 1 and None not in candidates else None


def socket_snapshot():
    import psutil
    started = time.time()
    try:
        rows = psutil.net_connections(kind="inet")
    except (psutil.Error, OSError):
        return Snapshot(started, (), False)
    if len(rows) > 16384:
        return Snapshot(started, (), False)
    paths = {}
    owners = []
    for row in rows:
        if not row.laddr or row.type not in {socket.SOCK_STREAM, socket.SOCK_DGRAM}:
            continue
        if row.pid not in paths:
            try:
                paths[row.pid] = canonical(psutil.Process(row.pid).exe()) if row.pid else None
            except (psutil.Error, OSError, ValueError):
                paths[row.pid] = None
        owners.append(SocketOwner("TCP" if row.type == socket.SOCK_STREAM else "UDP",
                                  row.laddr.ip.split("%")[0], row.laddr.port,
                                  row.raddr.ip.split("%")[0] if row.raddr else None,
                                  row.raddr.port if row.raddr else None, paths[row.pid], row.pid))
    return Snapshot(started, tuple(owners))
