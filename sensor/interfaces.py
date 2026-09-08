from dataclasses import dataclass
from ipaddress import ip_address
import socket

import psutil


@dataclass(frozen=True, slots=True)
class Interface:
    name: str
    ipv4: tuple[str, ...]
    is_up: bool
    loopback: bool | None
    candidate: bool


def list_interfaces() -> list[Interface]:
    stats = psutil.net_if_stats()
    result = []
    for name, addresses in psutil.net_if_addrs().items():
        ipv4 = tuple(a.address for a in addresses if a.family == socket.AF_INET)
        loopback = all(ip_address(a).is_loopback for a in ipv4) if ipv4 else None
        up = bool(name in stats and stats[name].isup)
        usable = any(not (ip_address(a).is_loopback or ip_address(a).is_link_local
                         or ip_address(a).is_unspecified) for a in ipv4)
        result.append(Interface(name, ipv4, up, loopback, up and usable))
    return result


def select_interface(name: str) -> Interface:
    for interface in list_interfaces():
        if interface.name == name:
            if not interface.is_up:
                raise ValueError(f"Interface {name!r} is down/disconnected")
            return interface
    raise ValueError(f"Interface {name!r} is unavailable; run interfaces")
