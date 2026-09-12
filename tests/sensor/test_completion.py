"""Deterministic failure injection and hand-calculated host feature contract."""
import threading
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from test_foundation import aggregator, packet
from test_capture import decoded
from scapy.all import IP, TCP
from sensor.capture import run_capture
from sensor.counters import Counters, calculate_rates
from sensor.features import host_features
from sensor.flows import MetadataQueue
from sensor.normalize import packet_to_metadata
from tcp_reference_live import reference_fields


class FeatureTests(unittest.TestCase):
    def test_seven_hand_calculated(self):
        agg = aggregator()
        agg.advance(9)
        agg.add(packet(packet_length=60))
        agg.add(packet(2, source_ip="198.51.100.2", destination_ip="192.0.2.1",
                       source_port=443, destination_port=1234, direction="inbound",
                       packet_length=100, tcp_syn=True))
        agg.add(packet(9, protocol="UDP", packet_length=40, tcp_syn=None))
        result = host_features(agg.advance(12)[0], {"192.0.2.1"})
        self.assertEqual(list(result.values()), [.3, 20., .5, 1, 1., 1/3, 200/3])

    def test_idle(self):
        self.assertEqual(list(host_features(aggregator().advance(12)[0], {"192.0.2.1"}).values()), [0]*7)

    def test_boundary(self):
        agg = aggregator()
        agg.advance(10)
        agg.add(packet(9.999))
        agg.add(packet(10))
        for end in (12, 22):
            self.assertEqual(host_features(agg.advance(end)[0], {"192.0.2.1"})["packets_per_second"], .1)

    def test_missing_headers(self):
        agg = aggregator()
        agg.advance(1)
        agg.add(packet(source_port=None))
        self.assertIsNone(host_features(agg.advance(12)[0], {"192.0.2.1"}))

    def test_unknown_context_and_shutdown(self):
        agg = aggregator()
        agg.advance(1)
        agg.add(packet())
        self.assertIsNone(host_features(agg.flush()[0], {"192.0.2.1"}))
        self.assertIsNone(host_features(aggregator().advance(12)[0], set()))

    def test_peers_deduplicate_across_protocols(self):
        agg = aggregator()
        agg.advance(1)
        for changes in ({}, {"protocol": "UDP"}, {"destination_ip": "203.0.113.3"}):
            agg.add(packet(**changes))
        self.assertEqual(host_features(agg.advance(12)[0], {"192.0.2.1"})["unique_remote_peers"], 2)


class FailureTests(unittest.TestCase):
    def test_independent_reference_parser(self):
        frame = decoded(IP(src="192.0.2.1", dst="198.51.100.2")/TCP(sport=1234, dport=80))
        self.assertEqual(reference_fields(bytes(frame)), ("192.0.2.1", "198.51.100.2", 1234, 80, 40))
        with self.assertRaises(ValueError):
            reference_fields(bytes(frame)[:30])

    def test_counter_wrap_is_invalid_not_corrected(self):
        result = calculate_rates(Counters(2**32-1, 0, 0, 0), Counters(3, 0, 0, 0), 1)
        self.assertEqual(result["reason"], "counter_reset")
        self.assertIsNone(result["delta"])

    def test_full_queue_pressure(self):
        queue = MetadataQueue()
        for _ in range(20007):
            queue.put(packet())
        self.assertEqual((len(queue), queue.high_water, queue.dropped), (20000, 20000, 7))

    def test_late_loss_invalidates_following_window(self):
        agg = aggregator()
        agg.advance(12)
        self.assertFalse(agg.add(packet()))
        self.assertTrue(agg.advance(22)[0].partial)

    def test_malformed_ip_length(self):
        malformed = decoded(IP(src="192.0.2.1", dst="198.51.100.2")/TCP())
        malformed[IP].len = 10
        with self.assertRaises(ValueError):
            packet_to_metadata(malformed, "fixture", {"192.0.2.1"})

    def test_unavailable_backend(self):
        with patch("sensor.capture.capture_preflight", side_effect=RuntimeError("backend unavailable")):
            with self.assertRaisesRegex(RuntimeError, "backend unavailable"):
                run_capture("fixture", 1, Mock())

    def lifecycle(self, fault):
        conf, sniffer = Mock(), Mock(running=True)
        sniffer.thread.is_alive.return_value = False
        output, stop = [], threading.Event()
        clock = [0.0]
        def sleep(_):
            clock[0] += 1.1
        def factory(**kw):
            def start():
                if fault == "malformed":
                    kw["prn"](object())
                if fault == "flow":
                    kw["prn"](decoded(IP(src="192.0.2.1", dst="198.51.100.2")/TCP(), 100))
                kw["started_callback"]()
            sniffer.start.side_effect = start
            return sniffer
        def emit(record):
            output.append(record)
            if fault == "requested" and record["type"] == "capture_started":
                stop.set()
            if fault == "worker" and record["type"] == "capture_started":
                sniffer.running = False
        with patch("sensor.capture.capture_preflight", return_value=conf), patch(
            "sensor.capture.resolve_capture_interface", return_value=(None, SimpleNamespace(network_name="fixture", index=23), {"192.0.2.1"})
        ), patch("scapy.all.AsyncSniffer", side_effect=factory), patch(
            "sensor.capture.read_counters", return_value=Counters(0, 0, 0, 0)
        ), patch("sensor.capture.time.monotonic", side_effect=lambda: clock[0]), patch(
            "sensor.capture.time.time", side_effect=lambda: 100 + clock[0] + (40 if fault == "clock" and clock[0] else 0)
        ), patch("sensor.capture.time.sleep", side_effect=sleep), patch(
            "sensor.capture.select_interface", side_effect=ValueError("unavailable") if fault == "adapter" else None,
            return_value=None
        ), patch("sensor.capture.local_addresses", return_value={"192.0.2.1"}):
            if fault in {"adapter", "clock", "worker", "flow"}:
                with self.assertRaises((ValueError, RuntimeError)):
                    run_capture("fixture", 3, emit, stop_event=stop)
            else:
                run_capture("fixture", 3, emit, stop_event=stop)
        conf.L2listen.return_value.close.assert_called_once()
        self.assertEqual(output[-1]["reason"], "error" if fault in {"adapter", "clock", "worker", "flow"} else "duration" if fault == "malformed" else fault)
        return output

    def test_adapter_disappears(self):
        self.lifecycle("adapter")

    def test_worker_disappears(self):
        self.lifecycle("worker")

    def test_flow_processing_failure_counted_and_closed(self):
        with patch("sensor.capture.WindowAggregator.add", side_effect=ValueError("injected flow fault")):
            output = self.lifecycle("flow")
        self.assertEqual(output[-1]["flow_errors"], 1)

    def test_parser_failure_counted_without_contents(self):
        output = self.lifecycle("malformed")
        self.assertEqual(output[-1]["parse_errors"], 1)
        self.assertNotIn("object at", str(output))

    def test_clock_jump(self):
        self.lifecycle("clock")

    def test_requested_shutdown(self):
        self.assertLess(self.lifecycle("requested")[-1]["shutdown_seconds"], 5)

    def test_genuinely_empty_running_capture(self):
        output = self.lifecycle("duration")
        health = [r for r in output if r["type"] == "health"]
        self.assertTrue(health)
        self.assertEqual(health[0]["capture_state"], "running")
        self.assertEqual(output[-1]["normalized"], 0)
