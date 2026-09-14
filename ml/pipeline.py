"""Bounded, reviewed, chronological host-v1 baseline workflow; never starts capture."""
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.detection.contract import FEATURE_NAMES, SCHEMA, MODEL_SCHEMA, PARAMETERS, aware, eligible, profile

MAX_ROWS = 20000
MIN_COUNTS = {"train": 180, "calibration": 60, "test": 60}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Input exceeds 64 MiB budget")
    def reject(value):
        raise ValueError("Non-finite JSON value: " + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject, object_pairs_hook=unique)


def write_json(path, value):
    # Never overwrite evidence, a review, a model manifest or a scored batch.
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def rows(dataset, mode="LIVE"):
    if dataset.get("schema") != "netsentinel-dataset-v1" or dataset.get("feature_order") != list(FEATURE_NAMES):
        raise ValueError("Dataset contract/order mismatch")
    records = dataset.get("rows")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_ROWS:
        raise ValueError("Need 1..20000 eligible records")
    seen, profiles, sessions = set(), [], {}
    for row in records:
        if set(row) != {"session", "window"}:
            raise ValueError("Only aggregate session/window rows accepted")
        session, window = row["session"], row["window"]
        if set(session) != {"session_id", "source_id", "run_id", "mode", "interface_name", "started_at", "observation_profile", "schema_version"}:
            raise ValueError("Exact session metadata required; arbitrary payload fields are forbidden")
        if set(window) != {"id", "session_id", "run_id", "mode", "interface_name", "start", "end", "finalized_at", "processed_at",
                           "measurement_source", "schema_version", "valid", "partial", "reason", "packets", "ip_bytes", "outbound_packets",
                           "inbound_packets", "outbound_bytes", "inbound_bytes", "tcp_packets", "udp_packets", "unknown_packets", "unknown_bytes",
                           "other_packets", "flow_count", "dropped", "kernel_loss", "features", "feature_schema_version", "capture_context"}:
            raise ValueError("Exact aggregate window metadata required; arbitrary payload fields are forbidden")
        if session["schema_version"] != "backend-v1" or window["schema_version"] != "backend-window-v1":
            raise ValueError("Persistence schema mismatch")
        if session["session_id"] in sessions and sessions[session["session_id"]] != session:
            raise ValueError("Session metadata changed within dataset")
        sessions[session["session_id"]] = session
        eligible(window)
        if aware(window["processed_at"]) > datetime.now(timezone.utc):
            raise ValueError("Future observations are not eligible")
        p = profile(session, window)
        if p["mode"] != mode:
            raise ValueError("LIVE/SIMULATION/REPLAY may not be mixed or relabelled")
        identity = (session["session_id"], aware(window["start"]).timestamp())
        if identity in seen:
            raise ValueError("Duplicate window in dataset")
        seen.add(identity)
        profiles.append(p)
    if any(p != profiles[0] for p in profiles):
        raise ValueError("One compatible source/interface/capture profile per model required")
    return sorted(records, key=lambda row: aware(row["window"]["start"]))


def validate(dataset, review, mode="LIVE"):
    records = rows(dataset, mode)
    if (set(review) != {"dataset_sha256", "reviewed_normal", "reviewer", "notes", "run_ids"}
            or review["dataset_sha256"] != digest(dataset) or review["reviewed_normal"] is not True
            or not isinstance(review["reviewer"], str) or not review["reviewer"].strip()
            or not isinstance(review["notes"], str) or len(review["notes"].strip()) < 20):
        raise ValueError("A dataset-bound operator review of ordinary benign activity is required")
    dataset_runs = sorted({r["session"]["run_id"] for r in records})
    if set(review["run_ids"]) != set(dataset_runs) or len(review["run_ids"]) != len(dataset_runs):
        raise ValueError("Review must cover every run exactly once")
    if len(records) < 300:
        raise ValueError("Insufficient baseline: at least 300 eligible windows required")
    if len(dataset_runs) < 3 or len({aware(r["window"]["start"]).astimezone(timezone.utc).date() for r in records}) < 2:
        raise ValueError("Insufficient baseline: at least three independent runs across two UTC dates")
    # Insertion/sorting follows chronological window start ordering
    for prev, nxt in zip(records, records[1:]):
        if aware(prev["window"]["end"]) > aware(nxt["window"]["start"]):
            raise ValueError("Interleaved/overlapping windows cannot establish chronological independence")
    splits = {
        "train": records[:180],
        "calibration": records[180:240],
        "test": records[240:300],
    }
    for name, subset in splits.items():
        if len(subset) < MIN_COUNTS[name]:
            raise ValueError(f"Insufficient {name} samples: {len(subset)} < {MIN_COUNTS[name]}")
        if sum(r["window"]["packets"] > 0 for r in subset) / len(subset) < .2:
            raise ValueError(f"{name} requires at least 20% observed non-idle windows")
    varying = sum(len({r["window"]["features"][name] for r in splits["train"]}) > 1 for name in FEATURE_NAMES)
    if varying < 2:
        raise ValueError("At least two varying training features required; constant traffic is not a useful baseline")
    return splits


def matrix(records):
    import numpy as np
    return np.asarray([eligible(r["window"]) for r in records], dtype=np.float64)


def distribution(scores):
    import numpy as np
    return {key: float(value) for key, value in zip(("min", "p50", "p95", "p99", "max"), np.quantile(scores, [0, .5, .95, .99, 1]))}


def train(dataset, review, directory, mode="LIVE"):
    import joblib
    import numpy as np
    import psutil
    import sklearn
    from sklearn.ensemble import IsolationForest
    splits = validate(dataset, review, mode)  # fail before creating an artifact
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    estimator = IsolationForest(**PARAMETERS).fit(matrix(splits["train"]))
    calibration = -estimator.score_samples(matrix(splits["calibration"]))
    threshold = float(np.quantile(calibration, .99, method="higher"))
    # Threshold/configuration are now frozen. Held-out data is scored once, never fitted.
    testing = -estimator.score_samples(matrix(splits["test"]))
    abnormal = testing > threshold
    per_run = []
    run_ids = [r["session"]["run_id"] for r in splits["test"]]
    for run in dict.fromkeys(run_ids):
        indices = [i for i, rid in enumerate(run_ids) if rid == run]
        count = int(sum(abnormal[indices]))
        per_run.append({"run_id": run, "windows": len(indices), "anomalous": count,
                        "anomalous_per_observed_hour": count / (len(indices) * 10 / 3600)})
    metadata = {
        "id": str(uuid4()), "schema": MODEL_SCHEMA, "feature_schema_version": SCHEMA,
        "feature_order": list(FEATURE_NAMES), "parameters": PARAMETERS, "preprocessing": "none",
        "score_semantics": "negative_score_samples; higher means more unusual; not attack probability",
        "threshold": threshold, "threshold_policy": "calibration_p99_higher_strict_greater_v1",
        "profile": profile(splits["train"][0]["session"], splits["train"][0]["window"]),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(splits["train"]), "dataset_sha256": digest(dataset), "review_sha256": digest(review),
        "sklearn_version": sklearn.__version__, "numpy_version": np.__version__,
        "python_version": platform.python_version(), "joblib_version": joblib.__version__,
        "training_evaluation_seconds": time.perf_counter() - started,
        "rss_after_bytes": psutil.Process().memory_info().rss,
        "splits": {name: {"count": len(rs), "run_ids": list(dict.fromkeys(r["session"]["run_id"] for r in rs)),
                          "first_start": rs[0]["window"]["start"], "last_end": rs[-1]["window"]["end"],
                          "sha256": digest(rs)} for name, rs in splits.items()},
        "evaluation": {"calibration_scores": distribution(calibration), "held_out_scores": distribution(testing),
                       "held_out_anomalous": int(sum(abnormal)), "held_out_count": len(testing),
                       "reviewed_normal_flag_fraction": float(np.mean(abnormal)), "per_run": per_run,
                       "limitations": "Operator-reviewed normal traffic only; no attack ground truth or classification accuracy. Small run counts limit generalization."},
    }
    artifact = directory / "model.joblib"
    joblib.dump({"metadata": metadata, "estimator": estimator}, artifact, compress=3)
    manifest = {**metadata, "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}
    from backend.detection.contract import validate_manifest
    validate_manifest(manifest)
    write_json(directory / "manifest.json", manifest)
    return manifest


def load(directory, trusted_sha256):
    import joblib
    import numpy as np
    import sklearn
    from sklearn.ensemble import IsolationForest
    from backend.detection.contract import validate_manifest
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    validate_manifest(manifest)
    if manifest["sklearn_version"] != sklearn.__version__ or manifest["numpy_version"] != np.__version__ or manifest["joblib_version"] != joblib.__version__:
        raise ValueError("Artifact environment mismatch")
    artifact = directory / "model.joblib"
    if artifact.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Artifact exceeds 64 MiB budget")
    actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual != trusted_sha256 or actual != manifest["artifact_sha256"]:
        raise ValueError("Trusted artifact digest mismatch; refusing deserialization")
    try:
        bundle = joblib.load(artifact)  # Only explicitly trusted LOCAL artifacts; pickle can execute code.
    except Exception as exc:
        raise ValueError("Malformed model artifact") from exc
    if not isinstance(bundle, dict) or set(bundle) != {"metadata", "estimator"}:
        raise ValueError("Malformed model bundle")
    if bundle["metadata"] != {k: v for k, v in manifest.items() if k != "artifact_sha256"}:
        raise ValueError("Manifest does not match trusted artifact")
    estimator = bundle["estimator"]
    if type(estimator) is not IsolationForest or estimator.n_features_in_ != 7 or any(estimator.get_params()[k] != v for k, v in PARAMETERS.items()):
        raise ValueError("Estimator contract mismatch")
    return estimator, manifest


def score(dataset, directory, trusted_sha256):
    from uuid import uuid5, NAMESPACE_URL
    estimator, manifest = load(directory, trusted_sha256)
    records = rows(dataset, manifest["profile"]["mode"])
    if profile(records[0]["session"], records[0]["window"]) != manifest["profile"]:
        raise ValueError("Model source/interface/observation profile mismatch")
    started = time.perf_counter()
    scores = -estimator.score_samples(matrix(records))
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for row, value in zip(records, scores):
        w = row["window"]
        results.append({"id": str(uuid5(NAMESPACE_URL, f"netsentinel:{w['id']}:{manifest['id']}")),
                        **{k: w[k] for k in ("session_id", "run_id", "mode", "interface_name")},
                        "window_id": w["id"], "model_version_id": manifest["id"],
                        "observed_at": w["end"], "scored_at": now, "anomaly_score": float(value),
                        "label": "ANOMALOUS" if value > manifest["threshold"] else "NORMAL"})
    return {"model_version_id": manifest["id"], "dataset_sha256": digest(dataset), "results": results,
            "scoring_seconds": time.perf_counter() - started,
            "notice": "Anomaly means deviation from baseline, not proof of attack or malware."}
