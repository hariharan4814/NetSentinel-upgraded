"""Offline stability-harness diagnostics; no sockets or capture devices opened."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import stability_live
from sensor.capture import run_capture
from sensor.counters import Counters
from test_foundation import packet


class StabilityTests(unittest.TestCase):
    def invoke(self, capture, *, addresses=None, percentile=None, cli_args=()):
        output = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(output))
            stack.enter_context(patch("sys.argv", ["stability_live.py", "--interface", "fixture", *cli_args]))
            stack.enter_context(patch.object(stability_live, "local_addresses",
                                            addresses or Mock(return_value={"192.0.2.1"})))
            stack.enter_context(patch.object(stability_live, "run_capture", side_effect=capture))
            # The controlled worker is exercised separately; never transmit here.
            stack.enter_context(patch.object(stability_live.threading, "Thread"))
            if percentile:
                stack.enter_context(patch.object(stability_live, "p95", side_effect=percentile))
            result = stability_live.main()
        return result, [json.loads(line) for line in output.getvalue().splitlines()]

    def test_capture_value_error_retains_message_and_traceback(self):
        def fail(interface, duration, emit, **kwargs):
            emit({"type": "capture_started"})
            private_local = b"DO-NOT-LOG-FRAME-LOCALS"
            raise ValueError("injected runtime failure")

        result, records = self.invoke(fail)
        self.assertEqual(result, 2)
        diagnostic = next(r for r in records if r["type"] == "validation_exception")
        self.assertEqual(diagnostic["exception_type"], "ValueError")
        self.assertEqual(diagnostic["exception_message"], "injected runtime failure")
        self.assertIn("test_stability_live.py", diagnostic["traceback"])
        self.assertIn("in fail", diagnostic["traceback"])
        self.assertIn("ValueError: injected runtime failure", diagnostic["traceback"])
        self.assertNotIn("DO-NOT-LOG-FRAME-LOCALS", json.dumps(records))
        self.assertEqual(diagnostic["phase"], "low_idle")
        self.assertGreaterEqual(diagnostic["elapsed_seconds"], 0)
        self.assertFalse(records[-1]["automated_checks_passed"])
        self.assertEqual(records[-1]["exception"], diagnostic)

    def test_preflight_exception_is_recorded(self):
        result, records = self.invoke(Mock(), addresses=Mock(side_effect=ValueError("bad address")))
        self.assertEqual(result, 2)
        self.assertEqual(records[-1]["phase"], "preflight")
        self.assertEqual(records[-1]["exception_message"], "bad address")

    def test_diagnostic_duration_cannot_pass_even_at_1800_seconds(self):
        clock = [0.0]
        def capture(interface, duration, emit, **kwargs):
            self.assertEqual(duration, 1800)
            emit({"type": "capture_started"})
            clock[0] = 1800
        with patch.object(stability_live.time, "monotonic", side_effect=lambda: clock[0]):
            result, records = self.invoke(capture, cli_args=("--diagnostic-seconds", "1800"))
        self.assertEqual(result, 2)
        self.assertTrue(records[-1]["diagnostic_only"])
        self.assertFalse(records[-1]["checks"]["duration"])

    def test_recovered_run_cannot_pass_clean_capture_or_reset_phase_clock(self):
        clock = [0.0]
        def recovered(interface, duration, emit, **kwargs):
            emit({"type": "capture_started"})
            clock[0] = 153
            emit({"type": "capture_status", "state": "INTERFACE_LOST"})
            clock[0] = 160
            emit({"type": "capture_restarted"})
            emit({"type": "capture_status", "state": "RUNNING"})
            clock[0] = 1800
            emit({"type": "capture_stopped", "reason": "duration", "interface_losses": 1,
                  "normalized": 0, "queue_high_water": 1, "flow_high_water": 1,
                  "window_high_water": 2, "peak_rss_bytes": 1000000, "shutdown_seconds": .01,
                  **{k: 0 for k in ("queue_dropped", "flow_overflow", "late", "parse_errors",
                                    "flow_errors", "queue_remaining", "shutdown_error")}})
        with patch.object(stability_live.time, "monotonic", side_effect=lambda: clock[0]):
            result, records = self.invoke(recovered)
        self.assertEqual(result, 2)
        summary = records[-1]
        self.assertEqual(summary["run_seconds"], 1800)
        self.assertTrue(summary["checks"]["duration"])
        self.assertIsNone(summary["error"])
        self.assertFalse(summary["checks"]["clean_capture"])

    def test_statistics_exception_is_recorded(self):
        result, records = self.invoke(Mock(), percentile=ValueError("bad statistic"))
        self.assertEqual(result, 2)
        self.assertEqual(records[-1]["stage"], "validation")
        self.assertIn("bad statistic", records[-1]["traceback"])

    def test_non_value_error_in_sample_aggregation_is_recorded(self):
        def malformed(interface, duration, emit, **kwargs):
            emit({"type": "capture_started"})
            emit({"type": "window", "flows": [{}]})
        result, records = self.invoke(malformed)
        self.assertEqual(result, 2)
        diagnostic = next(r for r in records if r["type"] == "validation_exception")
        self.assertEqual(diagnostic["exception_type"], "KeyError")
        self.assertIn("packets", diagnostic["exception_message"])

    def test_phase_boundaries(self):
        with patch.object(stability_live.time, "monotonic", return_value=100) as now:
            diagnostic = stability_live.Diagnostics()
            self.assertEqual(diagnostic.phase(), "preflight")
            diagnostic.started = 100
            for elapsed, phase in [(0, "low_idle"), (299.999, "low_idle"),
                                   (300, "controlled"), (367.172, "controlled"),
                                   (599.999, "controlled"), (600, "normal"), (1800, "normal")]:
                now.return_value = 100 + elapsed
                self.assertEqual(diagnostic.phase(), phase)

    def test_broken_stdout_uses_stderr_for_original_exception(self):
        output = io.StringIO()
        diagnostic = stability_live.Diagnostics()
        with patch("sys.stdout.write", side_effect=ValueError("closed output")), patch("sys.stderr", output):
            try:
                raise ValueError("original failure")
            except ValueError as exc:
                diagnostic.record(exc, source="capture")
        self.assertEqual(json.loads(output.getvalue())["exception_message"], "original failure")

    def controlled_worker(self, fault=None):
        clock, workers = [0.0], []

        class Event:
            def __init__(self):
                self.flag = False
            def set(self):
                self.flag = True
            def is_set(self):
                return self.flag
            def wait(self, seconds):
                if not self.flag:
                    clock[0] += seconds
                return self.flag

        def thread(**kwargs):
            workers.append(kwargs["target"])
            return Mock()

        def capture(interface, duration, emit, **kwargs):
            emit({"type": "capture_started"})
            workers[0]()  # Synchronous virtual time; no background thread.
            if isinstance(fault, ValueError):
                self.assertTrue(kwargs["stop_event"].is_set())

        output = io.StringIO()
        with redirect_stdout(output), patch("sys.argv", ["stability_live.py", "--interface", "fixture"]), patch.object(
            stability_live, "local_addresses", return_value={"192.0.2.1"}
        ), patch.object(stability_live, "run_capture", side_effect=capture), patch.object(
            stability_live.threading, "Thread", side_effect=thread
        ), patch.object(stability_live.threading, "Event", Event), patch.object(
            stability_live.time, "monotonic", side_effect=lambda: clock[0]
        ), patch.object(stability_live.socket, "socket") as sock:
            connection = sock.return_value.__enter__.return_value
            connection.connect.side_effect = fault
            connection.recv.return_value = b"HTTP/1.1 200 OK\r\n"
            self.assertEqual(stability_live.main(), 2)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_virtual_controlled_traffic_runs_sixty_attempts(self):
        summary = self.controlled_worker()[-1]
        self.assertEqual(summary["traffic_attempts"], 60)
        self.assertEqual(summary["traffic_successes"], 60)
        self.assertEqual(summary["traffic_errors"], 0)
        self.assertIsNone(summary["error"])

    def test_traffic_worker_value_error_is_reported_and_stops_run(self):
        records = self.controlled_worker(ValueError("injected traffic failure"))
        diagnostic = next(r for r in records if r["type"] == "validation_exception")
        self.assertEqual(diagnostic["phase"], "controlled")
        self.assertEqual(diagnostic["elapsed_seconds"], 300)
        self.assertEqual(diagnostic["stage"], "controlled_traffic")
        self.assertIn("in traffic", diagnostic["traceback"])
        self.assertEqual(records[-1]["error"], "ValueError")
        self.assertFalse(records[-1]["automated_checks_passed"])

    def test_expected_traffic_os_errors_remain_counted_and_are_explained(self):
        records = self.controlled_worker(OSError("injected network failure"))
        self.assertEqual(records[-1]["traffic_errors"], 60)
        self.assertEqual(len([r for r in records if r["type"] == "validation_exception"]), 60)
        self.assertFalse(records[-1]["checks"]["controlled_activity"])

    def test_virtual_1800_second_capture_and_harness(self):
        """Exercise real runner/aggregation with fake time, driver and OS metadata.

        This is deterministic coverage, never LIVE acceptance evidence. The
        controlled worker is disabled, so acceptance must remain false.
        """
        clock = [0.0]
        receiver = [None]
        conf, sniffer = Mock(), Mock(running=True)
        sniffer.thread.is_alive.return_value = False

        def factory(**kwargs):
            receiver[0] = kwargs["prn"]
            sniffer.start.side_effect = kwargs["started_callback"]
            return sniffer

        def tick(seconds):
            clock[0] += 1.1
            receiver[0](packet(1000 + clock[0], interface="fixture"))

        with ExitStack() as stack:
            for name, kwargs in [
                ("capture_preflight", {"return_value": conf}),
                ("resolve_capture_interface", {"return_value": (
                    None, SimpleNamespace(network_name="fixture", index=1), {"192.0.2.1"})}),
                ("select_interface", {"return_value": None}),
                ("local_addresses", {"return_value": {"192.0.2.1"}}),
                ("read_counters", {"return_value": Counters(0, 0, 0, 0)}),
                ("time.monotonic", {"side_effect": lambda: clock[0]}),
                ("time.time", {"side_effect": lambda: 1000 + clock[0]}),
                ("time.sleep", {"side_effect": tick}),
            ]:
                stack.enter_context(patch("sensor.capture." + name, **kwargs))
            stack.enter_context(patch("scapy.all.AsyncSniffer", side_effect=factory))
            stack.enter_context(patch("sensor.normalize.packet_to_metadata", side_effect=lambda p, *a: p))
            result, records = self.invoke(run_capture)
        summary = records[-1]
        self.assertEqual(result, 2)
        self.assertIsNone(summary["error"])
        self.assertEqual(summary["stopped"]["reason"], "duration")
        self.assertGreaterEqual(summary["run_seconds"], 1800)
        self.assertTrue(summary["checks"]["conservation"])
        self.assertTrue(summary["checks"]["bounds"])
        self.assertFalse(summary["checks"]["controlled_activity"])
        self.assertFalse(summary["automated_checks_passed"])
        self.assertEqual({r["phase"] for r in records if r["type"] == "health"},
                         {"low_idle", "controlled", "normal"})
        conf.L2listen.return_value.close.assert_called_once()

    def test_sample_coverage_threshold_and_validity_are_unchanged(self):
        for count, valid, expected in [(1669, True, False), (1699, True, False),
                                       (1700, True, True), (1700, False, False)]:
            with self.subTest(count=count, valid=valid):
                def capture(interface, duration, emit, **kwargs):
                    emit({"type": "capture_started"})
                    for index in range(count):
                        emit({"type": "health", "valid": valid if index == 0 else True,
                              "observed_at": stability_live.time.time(), "elapsed_seconds": 1})
                _, records = self.invoke(capture)
                self.assertEqual(records[-1]["checks"]["sample_coverage"], expected)

    def timed_sampling(self, duration, *, stall=False):
        """Real runner with bounded OS/output costs; no live device or traffic."""
        clock = [0.0]
        baseline = [None]
        output = []
        conf, sniffer = Mock(), Mock(running=True)
        sniffer.thread.is_alive.return_value = False

        def advance(seconds):
            clock[0] = round(clock[0] + seconds, 6)

        def factory(**kwargs):
            sniffer.start.side_effect = kwargs["started_callback"]
            return sniffer

        def counters(_):
            advance(.02)
            if baseline[0] is None:
                baseline[0] = clock[0]
            return Counters(round((clock[0] - baseline[0]) * 1000), 0, 0, 0)

        def emit(record):
            output.append(record)
            if record["type"] == "health":
                advance(4 if stall and len([r for r in output if r["type"] == "health"]) == 1 else .002)

        with ExitStack() as stack:
            for name, kwargs in [
                ("capture_preflight", {"return_value": conf}),
                ("resolve_capture_interface", {"return_value": (
                    None, SimpleNamespace(network_name="fixture", index=1), {"192.0.2.1"})}),
                ("select_interface", {"side_effect": lambda _: advance(.03)}),
                ("local_addresses", {"side_effect": lambda _: (advance(.01), {"192.0.2.1"})[1]}),
                ("read_counters", {"side_effect": counters}),
                ("time.monotonic", {"side_effect": lambda: clock[0]}),
                ("time.time", {"side_effect": lambda: 1000 + clock[0]}),
                ("time.sleep", {"side_effect": advance}),
                ("psutil.Process", {"return_value": SimpleNamespace(
                    cpu_percent=lambda: 0, memory_info=lambda: SimpleNamespace(rss=1000000))}),
            ]:
                stack.enter_context(patch("sensor.capture." + name, **kwargs))
            stack.enter_context(patch("scapy.all.AsyncSniffer", side_effect=factory))
            run_capture("fixture", duration, emit)
        return [r for r in output if r["type"] == "health"], output[-1]

    def test_sampling_cost_does_not_accumulate_over_thirty_minutes(self):
        samples, stopped = self.timed_sampling(1800)
        self.assertGreaterEqual(len(samples), 1700)
        self.assertLessEqual(len(samples), 1800)
        self.assertTrue(all(r["valid"] for r in samples))
        # Each counter delta uses the actual measurement interval, not 1 second.
        for record in samples:
            self.assertAlmostEqual(record["upload_bytes_per_second"], 1000, places=6)
        self.assertEqual(stopped["reason"], "duration")
        self.assertFalse(stopped["shutdown_error"])

    def test_sampling_stall_is_invalid_and_never_backfilled(self):
        samples, _ = self.timed_sampling(10, stall=True)
        self.assertGreaterEqual(samples[1]["elapsed_seconds"], 4)
        self.assertFalse(samples[1]["valid"])
        self.assertEqual(samples[1]["reason"], "sampling_gap")
        self.assertIsNone(samples[1]["delta"])
        self.assertLessEqual(len(samples), 6)
        self.assertTrue(all(r["valid"] for r in samples[2:]))
        self.assertTrue(all(b["observed_at"] - a["observed_at"] > .5
                            for a, b in zip(samples, samples[1:])))


if __name__ == "__main__":
    unittest.main()
