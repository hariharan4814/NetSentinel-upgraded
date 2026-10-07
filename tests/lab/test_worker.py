"""Worker security and lifecycle fixtures; no packet traffic or live controls."""
import json
import multiprocessing
import os
from pathlib import Path
import queue
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
import uuid
import psutil

from lab import worker
from lab.contracts import validate_config


def orphan_fit_fixture(path):
    Path(path).write_text(str(os.getpid()), encoding="ascii")
    worker.watch_owner(multiprocessing.parent_process())


def crashing_owner_fixture(path, release):
    child = multiprocessing.get_context("spawn").Process(target=orphan_fit_fixture, args=(path,))
    child.start()
    release.wait(timeout=20)
    os._exit(0)  # Deliberate fixture-only crash; bypasses normal child cleanup.


class WorkerTests(unittest.TestCase):
    def test_spawned_fit_exits_after_owner_abrupt_termination(self):
        context = multiprocessing.get_context("spawn")
        release = context.Event()
        identity = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture-child.pid"
            owner = context.Process(target=crashing_owner_fixture, args=(str(path), release))
            owner.start()
            try:
                deadline = time.monotonic() + 15
                while not path.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(path.exists(), "Spawned child did not become ready")
                identity = psutil.Process(int(path.read_text(encoding="ascii")))
                release.set()
                owner.join(timeout=10)
                self.assertFalse(owner.is_alive())
                deadline = time.monotonic() + 8
                while identity.is_running() and time.monotonic() < deadline:
                    time.sleep(0.1)
                self.assertFalse(identity.is_running(), "Fit survived its crashed owner")
            finally:
                release.set()
                if owner.is_alive():
                    owner.terminate()
                    owner.join(timeout=5)
                if identity is not None and identity.is_running():
                    identity.kill()
                    identity.wait(timeout=5)

    def test_dead_owner_exits_only_its_child(self):
        owner = MagicMock()
        owner.is_alive.side_effect = [True, False]
        with patch("lab.worker.time.sleep") as sleep, patch("lab.worker.os._exit") as exit_child:
            worker.watch_owner(owner)
        sleep.assert_called_once_with(1)
        exit_child.assert_called_once_with(1)

    def test_endpoint_is_fixed_loopback_without_credentials_paths_or_redirects(self):
        self.assertEqual(worker.endpoint("http://127.0.0.1:8811"), ("127.0.0.1", 8811))
        for url in ("https://localhost", "http://example.org", "http://user@localhost",
                    "http://localhost/api", "http://localhost/?x=1", "http://localhost/#x",
                    "http://localhost:65536", "file:///tmp/a"):
            with self.subTest(url=url), self.assertRaises(worker.WorkerError):
                worker.endpoint(url)

    def test_client_bounds_scope_response_and_redacts_transport_failures(self):
        client = worker.Client("http://127.0.0.1", "a" * 64)
        with self.assertRaises(worker.WorkerError):
            client.post("../../security", {})
        with patch("lab.worker.http.client.HTTPConnection") as connection:
            response = connection.return_value.getresponse.return_value
            response.status = 302
            response.read.return_value = b'{}'
            with self.assertRaises(worker.WorkerError):
                client.post("claim/", {})
            response.status = 200
            response.read.return_value = b'x' * 65537
            with self.assertRaises(worker.WorkerError):
                client.post("claim/", {})
            connection.return_value.request.side_effect = OSError("private credential aaaaa")
            with self.assertRaisesRegex(worker.WorkerError, "unavailable") as raised:
                client.post("claim/", {})
            self.assertNotIn("private", str(raised.exception))
            self.assertTrue(connection.return_value.close.called)

    def test_retention_removes_only_marked_uuid_direct_children(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unrelated = root / "keep"
            unrelated.mkdir()
            (unrelated / worker.MARKER).write_text("marker")
            unmarked = root / str(uuid.uuid4())
            unmarked.mkdir()
            owned = root / str(uuid.uuid4())
            owned.mkdir()
            (owned / worker.MARKER).write_text("marker")
            with patch.object(worker, "MAX_ARTIFACT_RUNS", 0):
                worker.prune(root)
            self.assertFalse(owned.exists())
            self.assertTrue(unrelated.is_dir())
            self.assertTrue(unmarked.is_dir())

    def test_disk_budget_never_deletes_unowned_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "preserve.txt"
            private.write_text("preserve")
            with patch.object(worker, "MAX_DISK_BYTES", 1), self.assertRaises(worker.WorkerError):
                worker.prune(root)
            self.assertEqual(private.read_text(), "preserve")

    def test_cancel_terminates_owned_process_and_records_cancelled(self):
        self.lifecycle(cancel=True, timeout=600, expected="CANCELLED")

    def test_timeout_terminates_owned_process_and_records_failed(self):
        self.lifecycle(cancel=False, timeout=0, expected="FAILED")

    def lifecycle(self, *, cancel, timeout, expected):
        client = MagicMock()
        client.post.return_value = {"cancel_requested": cancel}
        claim = {"job": {"id": str(uuid.uuid4()), "config": validate_config({})}, "lease_token": "b" * 64}
        context = MagicMock()
        context.Queue.return_value.get_nowait.side_effect = queue.Empty
        process = context.Process.return_value
        process.is_alive.side_effect = [True] * 10 + [False]
        with tempfile.TemporaryDirectory() as directory, patch("lab.worker.multiprocessing.get_context", return_value=context):
            self.assertEqual(worker.execute(client, claim, Path(directory), timeout=timeout), expected)
        process.terminate.assert_called_once()
        self.assertEqual(client.post.call_args.args[1]["status"], expected)
        self.assertNotIn("result", client.post.call_args.args[1])

    def test_invalid_claim_never_starts_child(self):
        with patch("lab.worker.multiprocessing.get_context") as context:
            with self.assertRaises(worker.WorkerError):
                worker.execute(MagicMock(), {"job": {"id": "../escape"}})
            context.assert_not_called()

    def test_pipeline_child_does_not_receive_worker_credential(self):
        import os
        def fake_pipeline(*args, **kwargs):
            self.assertNotIn("NETSENTINEL_LAB_WORKER_TOKEN", os.environ)
            return {"mode": "SIMULATION", "fixture": True}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NETSENTINEL_LAB_WORKER_TOKEN": "fixture-only"}), patch("lab.pipeline.run_experiment", fake_pipeline):
            worker.child_main({}, directory, queue.Queue())
            self.assertEqual(json.loads((Path(directory) / "_worker_result.json").read_bytes())["mode"], "SIMULATION")


if __name__ == "__main__":
    unittest.main()
