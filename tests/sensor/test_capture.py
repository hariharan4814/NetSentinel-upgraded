"""No network transmissions or live capture in unit tests."""
from dataclasses import asdict
import json
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scapy.all import ARP, Ether, IP, IPv6, TCP, UDP, Raw, ICMP
from scapy.layers.inet6 import IPv6ExtHdrFragment, IPv6ExtHdrHopByHop

from sensor.capture import check_driver_access, run_capture, resolve_capture_interface, stop_sniffer, window_record
from sensor.flows import WindowAggregator
from sensor.normalize import packet_to_metadata


def decoded(packet, timestamp=1):
    result = Ether(bytes(Ether()/packet))
    result.time = timestamp
    return result


def tcp(timestamp=1):
    return decoded(IP(src="192.0.2.1", dst="198.51.100.2")/
                   TCP(sport=50000, dport=443, flags="S")/Raw(b"PRIVATE-CONTENT"), timestamp)


class ConversionTests(unittest.TestCase):
    def test_ipv4_tcp(self):
        metadata = packet_to_metadata(tcp(), "fixture", {"192.0.2.1"})
        self.assertEqual((metadata.source_ip, metadata.destination_ip), ("192.0.2.1", "198.51.100.2"))
        self.assertEqual((metadata.source_port, metadata.destination_port), (50000, 443))
        self.assertEqual((metadata.protocol, metadata.packet_length, metadata.direction), ("TCP", 55, "outbound"))
        self.assertTrue(metadata.tcp_syn)
        self.assertFalse(metadata.incomplete)

    def test_udp(self):
        packet = decoded(IP(src="198.51.100.2", dst="192.0.2.1")/UDP(sport=53, dport=50001)/Raw(b"1234"))
        metadata = packet_to_metadata(packet, "fixture", {"192.0.2.1"})
        self.assertEqual((metadata.protocol, metadata.source_port, metadata.destination_port), ("UDP", 53, 50001))
        self.assertEqual((metadata.packet_length, metadata.direction), (32, "inbound"))

    def test_ipv6_extension(self):
        packet = decoded(IPv6(src="2001:db8::1", dst="2001:db8::2")/
                         IPv6ExtHdrHopByHop()/UDP(sport=1234, dport=53)/Raw(b"1234"))
        metadata = packet_to_metadata(packet, "fixture", {"2001:db8::1"})
        self.assertEqual((metadata.protocol, metadata.packet_length, metadata.source_port), ("UDP", 60, 1234))

    def test_non_ip(self):
        self.assertIsNone(packet_to_metadata(Ether()/ARP(), "fixture", set()))
        self.assertIsNone(packet_to_metadata(Raw(b"unsupported"), "fixture", set()))

    def test_payload_exclusion(self):
        metadata = packet_to_metadata(tcp(), "fixture", {"192.0.2.1"})
        self.assertNotIn("PRIVATE-CONTENT", json.dumps(asdict(metadata)))
        self.assertFalse(hasattr(metadata, "payload"))
        self.assertTrue(all(not isinstance(value, bytes) for value in asdict(metadata).values()))
        with self.assertRaises((AttributeError, TypeError)):
            metadata.payload = b"forbidden"

    def test_icmp_does_not_extract_embedded_tcp(self):
        packet = decoded(IP(src="198.51.100.2", dst="192.0.2.1")/ICMP(type=3)/
                         IP(src="192.0.2.1", dst="203.0.113.1")/TCP(sport=1, dport=443))
        metadata = packet_to_metadata(packet, "fixture", {"192.0.2.1"})
        self.assertEqual(metadata.protocol, "ICMP")
        self.assertIsNone(metadata.source_port)
        self.assertTrue(metadata.incomplete)

    def test_fragments_and_truncation(self):
        for packet in (
            decoded(IP(src="192.0.2.1", dst="198.51.100.2", proto=17, frag=1)/Raw(b"12345678")),
            decoded(IPv6(src="2001:db8::1", dst="2001:db8::2")/IPv6ExtHdrFragment(nh=17, offset=1)/Raw(b"12345678")),
        ):
            metadata = packet_to_metadata(packet, "fixture", {"192.0.2.1"})
            self.assertIsNone(metadata.source_port)
            self.assertTrue(metadata.incomplete)
        short = Ether(bytes(tcp())[:40])
        short.time = 1
        self.assertTrue(packet_to_metadata(short, "fixture", {"192.0.2.1"}).incomplete)

    def test_live_provenance_conversion_flow_boundaries(self):
        agg = WindowAggregator(start=0, mode="LIVE", session_id="synthetic-unit-only", interface="fixture")
        for timestamp in (9.999, 10):
            agg.advance(timestamp)
            agg.add(packet_to_metadata(tcp(timestamp), "fixture", {"192.0.2.1"}))
        first, = agg.advance(12)
        second, = agg.advance(22)
        for expected, window in ((0, first), (10, second)):
            record = window_record(window)
            self.assertEqual((record["start"], record["mode"]), (expected, "LIVE"))
            self.assertEqual(record["flows"][0]["packets"], 1)
            self.assertEqual(record["flows"][0]["ip_bytes"], 55)
            self.assertNotIn("PRIVATE-CONTENT", json.dumps(record))

    def test_loss_marks_future_idle_partial(self):
        agg = WindowAggregator(start=0, mode="LIVE", session_id="unit", interface="fixture")
        agg.mark_loss()
        self.assertTrue(agg.advance(12)[0].partial)


class LifecycleTests(unittest.TestCase):
    def test_admin_only_does_not_request_elevation(self):
        with patch("winreg.OpenKey"), patch("winreg.QueryValueEx", return_value=(1, 4)), patch(
            "sensor.capture.ctypes.windll.shell32.IsUserAnAdmin", return_value=0
        ):
            with self.assertRaisesRegex(RuntimeError, "automatic elevation is disabled"):
                check_driver_access()

    def test_unknown_driver_options_fail_closed(self):
        with patch("winreg.OpenKey", side_effect=OSError):
            with self.assertRaisesRegex(RuntimeError, "verify Npcap access"):
                check_driver_access()

    def test_invalid_interface_before_socket(self):
        conf = Mock()
        with patch("sensor.capture.select_interface", side_effect=ValueError("unavailable")):
            with self.assertRaises(ValueError):
                resolve_capture_interface("missing", conf)
        conf.L2listen.assert_not_called()

    def test_loopback_rejected(self):
        with patch("sensor.capture.select_interface"), patch("sensor.capture.local_addresses", return_value={"127.0.0.1", "::1"}):
            with self.assertRaisesRegex(ValueError, "non-loopback"):
                resolve_capture_interface("loopback", Mock())

    def test_duration_limits(self):
        for duration in (0, -1, 1801, float("nan")):
            with self.assertRaises(ValueError):
                run_capture("fixture", duration, Mock())

    def test_bounded_stop(self):
        sniffer = Mock(running=True)
        sniffer.thread.is_alive.return_value = False
        stop_sniffer(sniffer)
        sniffer.stop.assert_called_once_with(join=False)
        sniffer.join.assert_called_once_with(timeout=2)
        sniffer.thread.is_alive.return_value = True
        with self.assertRaises(RuntimeError):
            stop_sniffer(sniffer)

    def run_fake(self, interrupt=False, denied=False):
        conf = Mock()
        if denied:
            conf.L2listen.side_effect = PermissionError("sensitive third-party details")
        device = SimpleNamespace(network_name="fixture", index=23)
        output = []
        sniffer = Mock(running=True)
        sniffer.thread.is_alive.return_value = False

        def factory(**kwargs):
            self.assertFalse(kwargs["store"])
            def start():
                kwargs["prn"](tcp(time.time()))
                kwargs["started_callback"]()
            sniffer.start.side_effect = start
            return sniffer

        with patch("sensor.capture.capture_preflight", return_value=conf), patch(
            "sensor.capture.resolve_capture_interface", return_value=(None, device, {"192.0.2.1"})
        ), patch("scapy.all.AsyncSniffer", side_effect=factory), patch(
            "sensor.capture.time.sleep", side_effect=KeyboardInterrupt if interrupt else None
        ):
            if denied:
                with self.assertRaisesRegex(RuntimeError, "permissions") as exc:
                    run_capture("fixture", .001, output.append)
                self.assertNotIn("sensitive", str(exc.exception))
            else:
                run_capture("fixture", .001, output.append)
                sniffer.stop.assert_called_once_with(join=False)
                conf.L2listen.return_value.close.assert_called_once()
                self.assertFalse(output[-1]["shutdown_error"])
                self.assertEqual(output[-1]["reason"], "operator" if interrupt else "duration")
                self.assertEqual(output[-1]["normalized"], 1)
                self.assertEqual(sum(f["packets"] for r in output if r["type"] == "window"
                                     for f in r["flows"]), 1)

    def test_idle_duration_shutdown(self):
        self.run_fake()

    def test_ctrl_c_closes_capture(self):
        self.run_fake(interrupt=True)

    def test_permission_failure(self):
        self.run_fake(denied=True)


if __name__ == "__main__":
    unittest.main()
