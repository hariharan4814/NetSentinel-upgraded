"""Conservative address-family boundaries for approximate socket matching."""
import unittest
from companion.attribution import Snapshot, SocketOwner, match_packet
from sensor.models import PacketMetadata


class AddressFamilyAttributionTests(unittest.TestCase):
    def test_ipv6_only_wildcard_is_not_evidence_of_ipv4_socket_ownership(self):
        packet = PacketMetadata(1000, "fixture", "192.0.2.1", "198.51.100.1", 1500, 53, "UDP", 100, "outbound")
        owner = SocketOwner("UDP", "::", 1500, None, None, r"c:\fixture\app.exe")
        self.assertIsNone(match_packet(packet, Snapshot(1000, (owner,)), 1000))

    def test_ipv4_wildcard_does_not_match_ipv6_packet(self):
        packet = PacketMetadata(1000, "fixture", "2001:db8::1", "2001:db8::2", 1500, 53, "UDP", 100, "outbound")
        owner = SocketOwner("UDP", "0.0.0.0", 1500, None, None, r"c:\fixture\app.exe")
        self.assertIsNone(match_packet(packet, Snapshot(1000, (owner,)), 1000))
