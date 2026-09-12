"""Synthetic documentation-address fixtures; never transmit traffic."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from sensor.counters import Counters, calculate_rates
from sensor.flows import MetadataQueue, WindowAggregator, flow_key
from sensor.models import PacketMetadata, infer_direction
from sensor.cli import main


def packet(timestamp=1, **kwargs):
    return replace(PacketMetadata(timestamp, "fixture", "192.0.2.1", "198.51.100.2",
                                  1234, 443, "TCP", 60, "outbound", tcp_syn=True), **kwargs)


def aggregator(**kwargs):
    return WindowAggregator(start=0, mode="SIMULATION", session_id="fixture-1",
                            interface="fixture", **kwargs)


class FoundationTests(unittest.TestCase):
    def test_rates(self):
        result = calculate_rates(Counters(100, 200, 2, 3), Counters(300, 800, 4, 9), 2)
        self.assertEqual(result["upload_bytes_per_second"], 100)
        self.assertEqual(result["download_bytes_per_second"], 300)
        self.assertEqual(result["delta"]["packets_received"], 6)

    def test_resets_and_recovery(self):
        for index in range(4):
            values = [100] * 4
            values[index] = 1
            result = calculate_rates(Counters(50, 50, 50, 50), Counters(*values), 1)
            self.assertEqual(result["reason"], "counter_reset")
            self.assertIsNone(result["delta"])
        self.assertTrue(calculate_rates(Counters(1, 1, 1, 1), Counters(2, 2, 2, 2), 1)["valid"])

    def test_elapsed_and_gap(self):
        zero = Counters(0, 0, 0, 0)
        for elapsed in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                calculate_rates(zero, zero, elapsed)
        self.assertEqual(calculate_rates(zero, zero, 4)["reason"], "sampling_gap")

    def test_bidirectional_key(self):
        forward = packet()
        reverse = replace(forward, source_ip=forward.destination_ip,
                          destination_ip=forward.source_ip, source_port=443, destination_port=1234)
        self.assertEqual(flow_key(forward), flow_key(reverse))
        self.assertNotEqual(flow_key(forward), flow_key(replace(forward, protocol="UDP")))
        self.assertNotEqual(flow_key(forward), flow_key(replace(forward, interface="other")))

    def test_direction(self):
        self.assertEqual(infer_direction("192.0.2.1", "198.51.100.2", {"192.0.2.1"}), "outbound")
        self.assertEqual(infer_direction("198.51.100.2", "192.0.2.1", {"192.0.2.1"}), "inbound")
        self.assertEqual(infer_direction("192.0.2.1", "192.0.2.1", {"192.0.2.1"}), "unknown")

    def test_hand_calculated_window(self):
        agg = aggregator()
        agg.advance(9)
        agg.add(packet())
        agg.add(packet(2, source_ip="198.51.100.2", destination_ip="192.0.2.1",
                       source_port=443, destination_port=1234, packet_length=100,
                       direction="inbound", tcp_syn=False))
        agg.add(packet(9, protocol="UDP", packet_length=40, tcp_syn=None))
        self.assertEqual(agg.advance(11.9), [])
        window, = agg.advance(12)
        self.assertEqual(sum(f.packets for f in window.flows.values()), 3)
        self.assertEqual(sum(f.ip_bytes for f in window.flows.values()), 200)
        tcp = window.flows[flow_key(packet())]
        self.assertEqual((tcp.outbound_bytes, tcp.inbound_bytes, tcp.tcp_syn_packets), (60, 100, 1))
        self.assertFalse(window.partial)
        self.assertEqual(window.mode, "SIMULATION")

    def test_boundary_lateness_idle(self):
        agg = aggregator()
        agg.advance(10)
        agg.add(packet(10))
        agg.add(packet(9.9))
        old, = agg.advance(12)
        self.assertEqual(old.start, 0)
        self.assertFalse(agg.add(packet(9)))
        self.assertEqual(agg.late, 1)
        new, = agg.advance(22)
        self.assertEqual(new.start, 10)
        idle, = agg.advance(32)
        self.assertEqual(idle.flows, {})
        self.assertTrue(idle.partial)  # Known late loss invalidates remaining session.

    def test_flow_capacity_preserves_existing_key(self):
        agg = aggregator(max_flows=1)
        agg.advance(2)
        self.assertTrue(agg.add(packet()))
        self.assertFalse(agg.add(packet(destination_port=80)))
        self.assertTrue(agg.add(packet(2)))
        window, = agg.advance(12)
        self.assertEqual(len(window.flows), 1)
        self.assertEqual(window.dropped, 1)
        self.assertTrue(window.partial)
        self.assertEqual(next(iter(window.flows.values())).packets, 2)

    def test_queue_bound_and_oldest_drop(self):
        queue = MetadataQueue(2)
        for timestamp in (1, 2, 3):
            queue.put(packet(timestamp))
        self.assertEqual(len(queue), 2)
        self.assertEqual(queue.dropped, 1)
        self.assertEqual(queue.pop().timestamp, 2)
        self.assertEqual(queue.pop().timestamp, 3)
        self.assertIsNone(queue.pop())
        with self.assertRaises(TypeError):
            queue.put(b"payload")

    def test_clock_gap_and_shutdown(self):
        agg = aggregator()
        agg.advance(1)
        agg.add(packet())
        with self.assertRaises(ValueError):
            agg.advance(10000)
        window, = agg.flush()
        self.assertTrue(window.partial)
        self.assertEqual(len(agg.windows), 0)
        with self.assertRaises(ValueError):
            agg.add(packet())

    def test_missing_headers_and_ipv6(self):
        agg = aggregator()
        agg.advance(1)
        agg.add(packet(source_port=None, direction="unknown"))
        window, = agg.advance(12)
        self.assertTrue(window.partial)
        self.assertEqual(packet(source_ip="2001:0db8::1").source_ip, "2001:db8::1")

    def test_invalid_metadata_and_provenance(self):
        for change in ({"timestamp": float("nan")}, {"source_port": 65536}, {"packet_length": -1}):
            with self.assertRaises(ValueError):
                packet(**change)
        agg = aggregator()
        with self.assertRaises(ValueError):
            agg.add(packet())
        agg.advance(1)
        with self.assertRaises(ValueError):
            agg.add(packet(interface="wrong"))

    def test_ctrl_c(self):
        with patch("sensor.cli.list_interfaces", side_effect=KeyboardInterrupt):
            self.assertEqual(main(["interfaces"]), 0)

    def test_capture_preflight_no_socket(self):
        with patch("sensor.capture.Path.is_file", return_value=False):
            self.assertEqual(main(["capture", "--interface", "fixture"]), 2)


if __name__ == "__main__":
    unittest.main()
