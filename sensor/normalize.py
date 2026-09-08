"""Extract outer IP headers only; packet objects never leave this function."""
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6, IPv6ExtHdrFragment
from scapy.packet import NoPayload

from .models import PacketMetadata, infer_direction


def packet_to_metadata(packet, interface: str, local_ips: set[str]):
    layer = packet
    # Bounded link-layer walk; never search through encapsulated IP/ICMP data.
    for _ in range(8):
        if isinstance(layer, (IP, IPv6)):
            break
        if isinstance(layer, NoPayload):
            return None
        layer = layer.payload
    else:
        return None
    ip = layer
    incomplete = False
    if isinstance(ip, IP):
        length = int(ip.len)
        if ip.ihl is None or ip.ihl < 5 or length < ip.ihl * 4:
            raise ValueError("invalid IPv4 header length")
        number = int(ip.proto)
        fragmented = bool(ip.frag or ip.flags.MF)
        noninitial = bool(ip.frag)
        transport = ip.payload
    else:
        if ip.plen is None or ip.plen == 0:
            raise ValueError("IPv6 zero/jumbo length is unsupported")
        length = 40 + int(ip.plen)
        number, transport = int(ip.nh), ip.payload
        fragmented = noninitial = False
        for _ in range(8):
            if number not in {0, 43, 44, 60, 51}:
                break
            if not hasattr(transport, "nh"):
                incomplete = True
                break
            if isinstance(transport, IPv6ExtHdrFragment):
                fragmented = True
                noninitial = bool(transport.offset)
            number, transport = int(transport.nh), transport.payload
            if noninitial:
                break
        else:
            incomplete = True
    # original is transient capture memory: inspect length only.
    incomplete |= fragmented or (bool(ip.original) and len(ip.original) < length)
    protocol = {6: "TCP", 17: "UDP", 1: "ICMP", 58: "ICMPV6"}.get(number, "OTHER")
    sport = dport = syn = None
    if not noninitial and ((number == 6 and isinstance(transport, TCP)) or
                           (number == 17 and isinstance(transport, UDP))):
        sport, dport = int(transport.sport), int(transport.dport)
        if number == 6:
            syn = bool(transport.flags.S)
            incomplete |= transport.dataofs is None or transport.dataofs < 5
    elif number in {6, 17}:
        incomplete = True
    incomplete |= protocol in {"ICMP", "ICMPV6", "OTHER"}
    return PacketMetadata(float(packet.time), interface, ip.src, ip.dst, sport, dport,
                          protocol, length, infer_direction(ip.src, ip.dst, local_ips),
                          incomplete, syn)
