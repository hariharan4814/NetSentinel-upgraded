"""Virtual-time interface loss/recovery; no OS capture or network transmission."""
from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sensor.capture import run_capture, resolve_capture_interface
from sensor.counters import Counters
from sensor.interfaces import InterfaceUnavailable, select_interface, Interface
from test_foundation import packet


class RecoveryTests(unittest.TestCase):
    def exercise(self, *, recover_at=6, duration=12, timeout=10, retry=2,
                 changed_address=False, changed_guid=False, interrupt=False,
                 requested=False, malformed=False, slow_resolve=False, shutdown_failure=False,
                 lifecycle_diagnostics=False):
        clock = [0.0]
        output, workers, sockets, resolutions, normalized_contexts = [], [], [], [], []
        device = SimpleNamespace(network_name=r"\Device\NPF_{fixture}", index=23)
        conf = Mock()
        selected = Interface("fixture", ("192.0.2.1",), True, False, True)

        class Stop:
            flag = False
            def is_set(self):
                return self.flag
            def wait(self, seconds):
                if interrupt:
                    raise KeyboardInterrupt
                if requested:
                    self.flag = True
                    return True
                sleep(seconds)
                return self.flag

        stop = Stop()

        def check(name):
            if 2 <= clock[0] < recover_at:
                if malformed:
                    raise ValueError("malformed OS metadata")
                raise InterfaceUnavailable("Interface 'fixture' is down/disconnected")
            return selected

        def addresses(name):
            return {"192.0.2.9" if changed_address and clock[0] >= recover_at else "192.0.2.1"}

        def resolve(name, config):
            resolutions.append(clock[0])
            check(name)
            if slow_resolve and len(resolutions) > 1:
                clock[0] += timeout + 1
            resolved = SimpleNamespace(network_name=r"\Device\NPF_{replacement}", index=24) if (
                changed_guid and clock[0] >= recover_at) else device
            return selected, resolved, addresses(name)

        def socket_factory(**kwargs):
            self.assertFalse(kwargs["promisc"])
            self.assertEqual(kwargs["filter"], "ip or ip6")
            sock = Mock()
            sockets.append(sock)
            return sock

        conf.L2listen.side_effect = socket_factory

        def factory(**kwargs):
            self.assertFalse(kwargs["store"])
            worker = Mock(running=True)
            worker.thread.is_alive.return_value = shutdown_failure
            worker.stop.side_effect = lambda **kw: setattr(worker, "running", False)
            def start():
                kwargs["started_callback"]()
                # Real permitted metadata queued before loss must survive as partial.
                kwargs["prn"](packet(1000 + clock[0], interface=device.network_name,
                                    source_ip=next(iter(addresses("fixture")))))
            worker.start.side_effect = start
            workers.append(worker)
            return worker

        def sleep(seconds):
            clock[0] = round(clock[0] + seconds, 6)

        def normalize(p, interface, local):
            normalized_contexts.append(set(local))
            return p

        with ExitStack() as stack:
            for target, kwargs in [
                ("sensor.capture.capture_preflight", {"return_value": conf}),
                ("sensor.capture.resolve_capture_interface", {"side_effect": resolve}),
                ("sensor.capture.select_interface", {"side_effect": check}),
                ("sensor.capture.local_addresses", {"side_effect": addresses}),
                ("sensor.capture.read_counters", {"side_effect": lambda _: Counters(int(clock[0]*100), 0, 0, 0)}),
                ("sensor.capture.time.monotonic", {"side_effect": lambda: clock[0]}),
                ("sensor.capture.time.time", {"side_effect": lambda: 1000 + clock[0]}),
                ("sensor.capture.time.sleep", {"side_effect": sleep}),
                ("scapy.all.AsyncSniffer", {"side_effect": factory}),
                ("sensor.normalize.packet_to_metadata", {"side_effect": normalize}),
            ]:
                stack.enter_context(patch(target, **kwargs))
            if changed_guid or malformed or shutdown_failure:
                with self.assertRaisesRegex((ValueError, RuntimeError),
                                           "identity changed|malformed OS|shutdown failed"):
                    run_capture("fixture", duration, output.append, stop_event=stop,
                                recovery_retry_seconds=retry, recovery_timeout_seconds=timeout,
                                lifecycle_diagnostics=lifecycle_diagnostics)
            else:
                run_capture("fixture", duration, output.append, stop_event=stop,
                            recovery_retry_seconds=retry, recovery_timeout_seconds=timeout,
                            lifecycle_diagnostics=lifecycle_diagnostics)
        for sock in sockets:
            sock.close.assert_called_once()
        for worker in workers:
            worker.join.assert_called_with(timeout=2)
        return output, resolutions, workers, normalized_contexts, clock[0]

    def test_temporary_loss_and_successful_same_guid_recovery(self):
        output, resolutions, workers, _, _ = self.exercise()
        statuses = [r for r in output if r["type"] == "capture_status"]
        self.assertEqual([r["state"] for r in statuses],
                         ["RUNNING", "INTERFACE_LOST", "RECOVERING", "RECOVERING", "RUNNING", "STOPPED"])
        self.assertEqual(resolutions, [0, 4, 6])
        self.assertEqual(len(workers), 2)
        loss, recovered = statuses[1], statuses[-2]
        self.assertEqual(loss["loss_started_at"], 1002)
        self.assertIn("down/disconnected", loss["exception_message"])
        self.assertEqual(recovered["gap_seconds"], 4)
        self.assertNotEqual(loss["session_id"], recovered["session_id"])
        self.assertEqual(output[-1]["reason"], "duration")
        self.assertEqual(output[-1]["interface_losses"], 1)
        self.assertEqual(output[-1]["monitoring_gap_seconds"], 4)
        self.assertEqual(output[-1]["normalized"], 2)
        self.assertEqual(sum(f["packets"] for r in output if r["type"] == "window" for f in r["flows"]), 2)

    def test_opt_in_native_lifecycle_breadcrumb_order(self):
        output, *_ = self.exercise(lifecycle_diagnostics=True)
        events = [r for r in output if r["type"] == "capture_lifecycle"]
        expected = ["socket_open_begin", "socket_open_end", "worker_start_begin", "worker_ready",
                    "worker_stop_join_begin", "worker_stop_join_end", "socket_close_begin", "socket_close_end"]
        self.assertEqual([r["step"] for r in events], expected * 2)
        self.assertFalse(events[5]["worker_alive"])
        self.assertNotEqual(events[0]["session_id"], events[8]["session_id"])

    def test_no_fabricated_health_or_valid_windows_during_gap(self):
        output, *_ = self.exercise(duration=25)
        for r in output:
            if r["type"] == "health":
                self.assertFalse(1002 <= r["observed_at"] <= 1006)
            if r["type"] == "window" and r["start"] < 1006 and r["end"] > 1002:
                self.assertTrue(r["partial"])
                self.assertIsNone(r["features"])
        self.assertTrue(any(r["type"] == "window" for r in output))
        # A subsequent fully observed idle window is valid in the NEW session.
        complete = [r for r in output if r["type"] == "window" and not r["partial"]]
        self.assertTrue(complete)
        self.assertTrue(all(r["start"] >= 1010 and all(v == 0 for v in r["features"].values())
                            for r in complete))

    def test_recovery_refreshes_addresses_and_resets_counter_baseline(self):
        output, _, _, contexts, _ = self.exercise(changed_address=True)
        self.assertEqual(contexts, [{"192.0.2.1"}, {"192.0.2.9"}])
        restarted = next(r for r in output if r["type"] == "capture_restarted")
        samples = [r for r in output if r["type"] == "health" and r["session_id"] == restarted["session_id"]]
        self.assertTrue(samples)
        self.assertEqual(samples[0]["delta"]["bytes_sent"], 100)
        self.assertTrue(samples[0]["valid"])
        windows = [r for r in output if r["type"] == "window" and r["session_id"] == restarted["session_id"]]
        self.assertEqual(windows[0]["local_addresses"], ["192.0.2.9"])

    def test_timeout_and_bounded_retry_intervals(self):
        output, resolutions, workers, _, elapsed = self.exercise(recover_at=100, timeout=5)
        self.assertEqual(resolutions, [0, 4, 6])
        self.assertEqual(elapsed, 7)
        self.assertEqual(len(workers), 1)
        self.assertEqual(output[-1]["reason"], "interface_unavailable")
        self.assertEqual(output[-1]["recovery_attempts"], 2)
        self.assertFalse(output[-1]["shutdown_error"])
        self.assertIn("down/disconnected", output[-1]["diagnostic"]["exception_message"])

    def test_duration_deadline_limits_recovery(self):
        output, _, _, _, elapsed = self.exercise(recover_at=100, timeout=30, duration=5)
        self.assertEqual(elapsed, 5)
        self.assertEqual(output[-1]["reason"], "interface_unavailable")

    def test_zero_timeout_disables_retries(self):
        output, resolutions, _, _, elapsed = self.exercise(timeout=0)
        self.assertEqual(resolutions, [0])
        self.assertEqual(elapsed, 2)
        self.assertEqual(output[-1]["reason"], "interface_unavailable")

    def test_requested_shutdown_during_recovery(self):
        output, resolutions, _, _, elapsed = self.exercise(requested=True)
        self.assertEqual(output[-1]["reason"], "requested")
        self.assertEqual(resolutions, [0])
        self.assertEqual(elapsed, 2)

    def test_ctrl_c_during_recovery(self):
        output, resolutions, _, _, elapsed = self.exercise(interrupt=True)
        self.assertEqual(output[-1]["reason"], "operator")
        self.assertEqual(resolutions, [0])
        self.assertEqual(elapsed, 2)

    def test_replacement_guid_never_opens_socket(self):
        output, _, workers, _, _ = self.exercise(changed_guid=True)
        self.assertEqual(len(workers), 1)
        self.assertEqual(output[-1]["reason"], "error")

    def test_generic_value_error_is_not_treated_as_interface_loss(self):
        output, resolutions, _, _, _ = self.exercise(malformed=True)
        self.assertEqual(resolutions, [0])
        self.assertEqual(output[-1]["reason"], "error")
        self.assertEqual(output[-1]["interface_losses"], 0)

    def test_slow_revalidation_cannot_restart_after_recovery_deadline(self):
        output, _, workers, _, _ = self.exercise(recover_at=4, timeout=5, slow_resolve=True)
        self.assertEqual(len(workers), 1)
        self.assertEqual(output[-1]["reason"], "interface_unavailable")

    def test_shutdown_failure_prevents_recovery(self):
        output, resolutions, workers, _, _ = self.exercise(shutdown_failure=True)
        self.assertEqual(resolutions, [0])
        self.assertEqual(len(workers), 1)
        self.assertTrue(output[-1]["shutdown_error"])
        self.assertEqual(output[-1]["reason"], "error")

    def test_invalid_recovery_configuration_fails_before_capture(self):
        with patch("sensor.capture.capture_preflight") as preflight:
            for kwargs in ({"recovery_retry_seconds": 0}, {"recovery_retry_seconds": float("nan")},
                           {"recovery_timeout_seconds": -1}, {"recovery_timeout_seconds": 301}):
                with self.assertRaises(ValueError):
                    run_capture("fixture", 10, Mock(), **kwargs)
            preflight.assert_not_called()

    def test_selected_down_interface_has_typed_diagnostic(self):
        with patch("sensor.interfaces.list_interfaces", return_value=[
            Interface("Wi-Fi", ("192.0.2.1",), False, False, False)
        ]):
            with self.assertRaisesRegex(InterfaceUnavailable, "Wi-Fi.*down/disconnected"):
                select_interface("Wi-Fi")

    def test_missing_npcap_mapping_is_unavailable_but_ambiguity_is_fatal(self):
        conf, api = Mock(), Mock()
        api.ConvertInterfaceAliasToLuid.return_value = 0
        def index(luid, result):
            result._obj.value = 23
            return 0
        api.ConvertInterfaceLuidToIndex.side_effect = index
        with patch("sensor.capture.select_interface"), patch(
            "sensor.capture.local_addresses", return_value={"192.0.2.1"}
        ), patch("sensor.capture.ctypes.windll.iphlpapi", api):
            conf.ifaces.values.return_value = []
            with self.assertRaisesRegex(InterfaceUnavailable, "no Npcap mapping"):
                resolve_capture_interface("Wi-Fi", conf)
            device = SimpleNamespace(index=23, name="Wi-Fi", network_name=r"\Device\NPF_{fixture}")
            conf.ifaces.values.return_value = [device, device]
            with self.assertRaises(ValueError) as caught:
                resolve_capture_interface("Wi-Fi", conf)
            self.assertNotIsInstance(caught.exception, InterfaceUnavailable)


if __name__ == "__main__":
    unittest.main()
