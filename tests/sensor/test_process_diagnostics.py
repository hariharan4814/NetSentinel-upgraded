"""Process evidence tests use disposable children, never capture or traffic."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from process_diagnostics import ProcessDiagnostics
from stability_live import Diagnostics
from stability_observer import exit_fields, observe


class ProcessEvidenceTests(unittest.TestCase):
    def test_signed_and_unsigned_exit_code_are_preserved(self):
        self.assertEqual(exit_fields(-1)["exit_hex"], "0xFFFFFFFF")
        self.assertEqual(exit_fields(0xffffffff)["exit_signed"], -1)
        self.assertEqual(exit_fields(0xc0000005)["exit_hex"], "0xC0000005")
        self.assertNotEqual(exit_fields(-1)["exit_hex"], "0xC0000005")

    def test_system_exit_is_diagnosed_without_replacing_exit_code(self):
        output = io.StringIO()
        with redirect_stdout(output), patch("sys.argv", ["stability_live.py", "--interface", "fixture"]), patch(
            "stability_live.validate", side_effect=SystemExit(-1)
        ):
            from stability_live import main
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, -1)
        diagnostic = json.loads(output.getvalue())
        self.assertEqual(diagnostic["exception_type"], "SystemExit")
        self.assertEqual(diagnostic["exception_message"], "-1")

    def test_thread_base_exception_and_metadata_only_journal(self):
        old_hook = threading.excepthook
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            diagnostic = Diagnostics()
            process = ProcessDiagnostics(directory, diagnostic)
            diagnostic.process = process
            try:
                process.observe({"type": "health", "valid": True, "flows": ["PRIVATE"], "payload": "PRIVATE"})
                process.observe({"type": "window", "flows": ["PRIVATE"]})
                def fail():
                    raise SystemExit(7)
                worker = threading.Thread(target=fail)
                worker.start()
                worker.join(2)
                self.assertFalse(worker.is_alive())
            finally:
                process.close()
            content = (Path(directory) / "process.jsonl").read_text()
            self.assertNotIn("PRIVATE", content)
            records = [json.loads(line) for line in content.splitlines()]
            failure = next(r for r in records if r["type"] == "validation_exception")
            self.assertEqual(failure["exception_type"], "SystemExit")
            self.assertEqual(failure["stage"], "uncaught_thread")
            self.assertEqual(failure["pid"], os.getpid())
        self.assertIs(threading.excepthook, old_hook)

    def run_child(self, sudden):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            script = (
                "import sys, os\n"
                f"sys.path.insert(0, {str(Path(__file__).parent)!r})\n"
                "from process_diagnostics import ProcessDiagnostics\n"
                "from stability_live import Diagnostics\n"
                f"p = ProcessDiagnostics({directory!r}, Diagnostics())\n"
                "print('{\"type\":\"health\",\"run_elapsed_seconds\":270.016}', flush=True)\n"
            )
            if sudden:
                script += "os._exit(-1)\n"  # Only this disposable test child; not a diagnosis of the real failure.
            else:
                script += "p.write({'type':'validator_returned','exit_code':2})\nprint('{\"type\":\"stability_summary\"}', flush=True)\nraise SystemExit(2)\n"
            result = observe([sys.executable, "-u", "-X", "faulthandler", "-c", script], directory, 10)
            journal = [json.loads(line) for line in (Path(directory) / "process.jsonl").read_text().splitlines()]
            observer = [json.loads(line) for line in (Path(directory) / "observer.jsonl").read_text().splitlines()]
        return result, journal, observer

    def test_observer_retains_exit_when_child_bypasses_all_finalizers(self):
        result, journal, observer = self.run_child(True)
        self.assertEqual(result["exit_unsigned"], 0xffffffff if os.name == "nt" else 255)
        self.assertFalse(result["final_summary_present"])
        self.assertEqual(result["last_stdout_event"]["type"], "health")
        self.assertNotIn("interpreter_atexit", [r["type"] for r in journal])
        self.assertEqual(observer[-1]["type"], "observer_child_exited")
        self.assertIsNone(result["observer_action"])

    def test_observer_distinguishes_normal_diagnostic_exit(self):
        result, journal, _ = self.run_child(False)
        self.assertEqual(result["child_returncode"], 2)
        self.assertTrue(result["final_summary_present"])
        self.assertIn("interpreter_atexit", [r["type"] for r in journal])

    def test_observer_timeout_records_its_own_intervention(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            result = observe([sys.executable, "-c", "import time; time.sleep(30)"], directory, .2)
            records = [json.loads(line) for line in (Path(directory) / "observer.jsonl").read_text().splitlines()]
        self.assertEqual(result["observer_action"], "timeout")
        self.assertEqual(records[-2]["type"], "observer_termination_requested")


if __name__ == "__main__":
    unittest.main()
