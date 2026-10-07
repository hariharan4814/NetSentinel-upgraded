"""Independent loopback worker; Django never imports the model-fitting runtime.

Run from the repository root with NETSENTINEL_LAB_WORKER_TOKEN in the environment.
Ctrl+C terminates only this worker's child, then requests cancellation. A lost
backend/worker is recovered by the 30-second database lease, never by fake success.
"""
import argparse
import http.client
import json
import multiprocessing
import os
from pathlib import Path
import queue
import re
import shutil
import sys
import threading
import time
from urllib.parse import urlsplit
import uuid

from .contracts import MAX_RESULT_BYTES, canonical_json, validate_config

MAX_DISK_BYTES = 500 * 1024 * 1024
MAX_ARTIFACT_RUNS = 20
DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "artifacts" / "lab"
MARKER = ".netsentinel-lab-owned"
MAX_JOB_SECONDS = 600


class WorkerError(Exception):
    pass


def endpoint(base_url):
    try:
        parsed = urlsplit(base_url)
        port = parsed.port or 8001
    except (ValueError, AttributeError):
        raise WorkerError("Use a loopback HTTP base URL.") from None
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"} or not 1 <= port <= 65535):
        raise WorkerError("Use a loopback HTTP base URL without paths or credentials.")
    return parsed.hostname, port


class Client:
    def __init__(self, base_url, token):
        self.host, self.port = endpoint(base_url)
        if (not isinstance(token, str) or not 32 <= len(token) <= 256 or not token.isascii()
                or any(ord(c) <= 32 or ord(c) == 127 for c in token) or token.startswith("replace-with-")):
            raise WorkerError("Configure the distinct NETSENTINEL_LAB_WORKER_TOKEN environment variable.")
        self.token = token

    def post(self, action, body):
        if not re.fullmatch(r"claim/|[a-f0-9-]{36}/(?:heartbeat|finish)/", action):
            raise WorkerError("Unsupported worker action.")
        encoded = canonical_json(body)
        if len(encoded) > MAX_RESULT_BYTES:
            raise WorkerError("Worker request exceeded its size limit.")
        # http.client ignores HTTP(S)_PROXY and never follows redirects.
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        try:
            connection.request("POST", "/api/v1/lab/worker/" + action, encoded,
                               {"Authorization": "Bearer " + self.token,
                                "Content-Type": "application/json"})
            response = connection.getresponse()
            payload = response.read(65537)
            if response.status != 200 or len(payload) > 65536:
                raise WorkerError("Local worker API rejected the request or is unavailable.")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise WorkerError("Invalid local worker response.")
            return data
        except (OSError, ValueError, http.client.HTTPException):
            raise WorkerError("Local worker API is unavailable or returned invalid JSON.") from None
        finally:
            connection.close()


def owned_directories(root):
    """Only directories created by this worker are eligible for retention cleanup."""
    found = []
    for path in root.iterdir():
        if path.is_symlink() or not path.is_dir() or not (path / MARKER).is_file():
            continue
        try:
            uuid.UUID(path.name)
        except ValueError:
            continue
        if path.resolve().parent != root.resolve():
            continue
        found.append(path)
    return sorted(found, key=lambda item: item.stat().st_mtime)


def directory_bytes(path):
    total = 0
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
        for name in files:
            child = Path(directory) / name
            if not child.is_symlink():
                try:
                    total += child.stat().st_size
                except FileNotFoundError:
                    pass  # A child atomically replacing a result is not a disk failure.
    return total


def prune(root, *, reserve=0):
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise WorkerError("Artifact root must not be a symlink.")
    directories = owned_directories(root)
    while directories and (len(directories) > MAX_ARTIFACT_RUNS - reserve or directory_bytes(root) > MAX_DISK_BYTES):
        path = directories.pop(0)
        # Recheck the final resolved target immediately before recursive removal.
        if path.is_symlink() or path.resolve().parent != root.resolve() or not (path / MARKER).is_file():
            raise WorkerError("Artifact ownership changed during cleanup.")
        shutil.rmtree(path)
    if directory_bytes(root) > MAX_DISK_BYTES:
        raise WorkerError("Artifact storage is full; unrelated files were preserved.")


def watch_owner(owner):
    """A crashed worker cannot leave a model fit running as an orphan.

    multiprocessing's parent handle checks process identity, not a reusable PID.
    The daemon thread runs only inside our owned fit child and exits that child.
    """
    while owner.is_alive():
        time.sleep(1)
    os._exit(1)


def child_main(config, output_dir, updates):
    # Libraries performing training have no reason to see the worker credential.
    os.environ.pop("NETSENTINEL_LAB_WORKER_TOKEN", None)
    owner = multiprocessing.parent_process()
    if owner is not None:
        threading.Thread(target=watch_owner, args=(owner,), daemon=True).start()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"

    def progress(stage, completed=None, total=None):
        try:
            updates.put_nowait({"stage": stage, "completed": completed, "total": total})
        except queue.Full:
            pass  # Latest progress is best effort; never block training on its UI.

    try:
        from .pipeline import run_experiment
        result = run_experiment(config, output_dir=output_dir, progress=progress)
        payload = canonical_json(result)
        if len(payload) > MAX_RESULT_BYTES - 1024:
            raise WorkerError("Result too large")
        target = Path(output_dir) / "_worker_result.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(payload)
        temporary.replace(target)
    except BaseException:
        # Do not print arbitrary library exceptions: they may contain paths or
        # data. A nonzero exit leads to a generic, explicit FAILED job.
        sys.exit(1)


def terminate_child(process):
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join(timeout=5)


def execute(client, claim, root=DEFAULT_ROOT, *, timeout=MAX_JOB_SECONDS):
    job = claim.get("job")
    if not isinstance(job, dict):
        raise WorkerError("Invalid job claim.")
    try:
        job_id = str(uuid.UUID(job["id"]))
        lease = claim["lease_token"]
        if not isinstance(lease, str) or not re.fullmatch(r"[0-9a-f]{64}", lease):
            raise ValueError()
        config = validate_config(job["config"])
    except (KeyError, ValueError, TypeError, AttributeError):
        raise WorkerError("Invalid job claim.") from None
    root = Path(root)
    process = None
    updates = None
    status, result = "FAILED", None
    interrupted = False
    try:
        prune(root, reserve=1)
        destination = root / job_id
        # A restart never resumes/overwrites an old fit with the same identity.
        destination.mkdir(exist_ok=False)
        (destination / MARKER).write_text("NetSentinel SIMULATION worker artifacts\n", encoding="utf-8")
        context = multiprocessing.get_context("spawn")
        updates = context.Queue(maxsize=32)
        process = context.Process(target=child_main, args=(config, str(destination), updates))
        process.start()
        started = time.monotonic()
        last_heartbeat = started - 5
        progress = {"stage": "starting", "completed": None, "total": None}
        while True:
            while True:
                try:
                    progress = updates.get_nowait()
                except queue.Empty:
                    break
            now = time.monotonic()
            if now - last_heartbeat >= 5 or not process.is_alive():
                response = client.post(job_id + "/heartbeat/", {"lease_token": lease, **progress})
                last_heartbeat = now
                if response.get("cancel_requested") is True:
                    status = "CANCELLED"
                    break
                if directory_bytes(root) > MAX_DISK_BYTES:
                    raise WorkerError("Artifact storage budget exceeded.")
            if not process.is_alive():
                process.join(timeout=1)
                target = destination / "_worker_result.json"
                if process.exitcode == 0 and target.is_file() and target.stat().st_size <= MAX_RESULT_BYTES - 1024:
                    result = json.loads(target.read_bytes())
                    status = "SUCCEEDED"
                break
            if now - started >= timeout:
                raise WorkerError("Experiment exceeded its execution time budget.")
            time.sleep(0.1)
    except KeyboardInterrupt:
        status, interrupted = "CANCELLED", True
    except (WorkerError, OSError, ValueError):
        status, result = "FAILED", None
    finally:
        if process is not None:
            terminate_child(process)
        if updates is not None:
            updates.close()
            updates.cancel_join_thread()
    body = {"lease_token": lease, "status": status}
    if status == "SUCCEEDED":
        body["result"] = result
    try:
        client.post(job_id + "/finish/", body)
    finally:
        prune(root)
    if interrupted:
        raise KeyboardInterrupt
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ROOT,
                        help="Local worker-owned artifact directory; never accepted from HTTP.")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job, then exit.")
    args = parser.parse_args(argv)
    try:
        client = Client(args.base_url, os.environ.get("NETSENTINEL_LAB_WORKER_TOKEN", ""))
        print("NetSentinel SIMULATION worker started; Ctrl+C stops this worker and its own current job.")
        while True:
            claim = client.post("claim/", {})
            if claim.get("job") is not None:
                status = execute(client, claim, args.artifact_root)
                print("Experiment finished:", status)
            if args.once:
                return 0
            time.sleep(2)
    except KeyboardInterrupt:
        print("Worker stopped. Any unreachable job expires through its bounded lease.")
        return 0
    except WorkerError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
