"""Seven host-v1 values reconstructed only from finalized flow statistics."""
from .models import infer_direction

FEATURE_NAMES = ("packets_per_second", "ip_bytes_per_second", "outbound_byte_fraction",
                 "unique_remote_peers", "tcp_syn_fraction", "udp_fraction", "mean_ip_packet_bytes")


def host_features(window, local_ips):
    if window.partial or window.finalized_at is None or not local_ips:
        return None
    packets = size = outbound = inbound = tcp = syn = udp = 0
    peers = set()  # At most two endpoints per capped flow entry.
    for key, flow in window.flows.items():
        direction = infer_direction(key[2][0], key[3][0], local_ips)
        if flow.incomplete or flow.unknown_packets or direction == "unknown":
            return None
        peers.add(key[3][0] if direction == "outbound" else key[2][0])
        packets += flow.packets
        size += flow.ip_bytes
        outbound += flow.outbound_bytes
        inbound += flow.inbound_bytes
        if key[1] == "TCP":
            tcp += flow.packets
            syn += flow.tcp_syn_packets
        elif key[1] == "UDP":
            udp += flow.packets
    values = (packets / 10, size / 10, outbound / (outbound + inbound) if outbound + inbound else 0.0,
              len(peers), syn / tcp if tcp else 0.0, udp / packets if packets else 0.0,
              size / packets if packets else 0.0)
    return dict(zip(FEATURE_NAMES, values))
