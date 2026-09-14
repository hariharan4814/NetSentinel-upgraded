"""Dependency-free host-v1 validation shared by the API and offline ML workflow."""
import ipaddress
import math
from datetime import datetime
from uuid import UUID

FEATURE_NAMES = (
    "packets_per_second", "ip_bytes_per_second", "outbound_byte_fraction",
    "unique_remote_peers", "tcp_syn_fraction", "udp_fraction", "mean_ip_packet_bytes",
)
SCHEMA = "host-v1"
MODEL_SCHEMA = "iforest-host-v1"
MODES = ("LIVE", "SIMULATION", "REPLAY")
PARAMETERS = {"n_estimators": 100, "max_samples": 256, "contamination": "auto", "random_state": 42, "n_jobs": 1}


def validate_manifest(value):
    """Validate the bounded metadata document BEFORE any artifact deserialization."""
    import json
    import re
    required = {"id", "schema", "feature_schema_version", "feature_order", "parameters", "preprocessing",
                "score_semantics", "threshold", "threshold_policy", "profile", "trained_at", "sample_count",
                "dataset_sha256", "review_sha256", "sklearn_version", "numpy_version", "python_version",
                "joblib_version", "training_evaluation_seconds", "rss_after_bytes", "splits", "evaluation", "artifact_sha256"}
    if not isinstance(value, dict) or set(value) != required or len(json.dumps(value, allow_nan=False)) > 48000:
        raise ValueError("Missing, extra or oversized model metadata")
    if value["schema"] != MODEL_SCHEMA or value["feature_schema_version"] != SCHEMA or value["feature_order"] != list(FEATURE_NAMES):
        raise ValueError("Model schema/feature order mismatch")
    if value["parameters"] != PARAMETERS or value["preprocessing"] != "none" or value["threshold_policy"] != "calibration_p99_higher_strict_greater_v1":
        raise ValueError("Unsupported estimator/threshold configuration")
    UUID(value["id"])
    aware(value["trained_at"])
    if not 0 <= finite(value["threshold"]) <= 1 or type(value["sample_count"]) is not int or value["sample_count"] < 180:
        raise ValueError("Invalid model threshold/training count")
    for key in ("artifact_sha256", "dataset_sha256", "review_sha256"):
        if not isinstance(value[key], str) or not re.fullmatch(r"[0-9a-f]{64}", value[key]):
            raise ValueError("SHA-256 digest required")
    p = value["profile"]
    if not isinstance(p, dict) or set(p) != {"source_id", "mode", "interface_name", "observation_profile", "capture_interface", "interface_index", "filter", "promiscuous", "flow_schema_version"}:
        raise ValueError("Complete model profile required")
    UUID(p["source_id"])
    if p["mode"] not in MODES or not p["interface_name"] or not p["observation_profile"]:
        raise ValueError("Invalid model provenance")
    context({k: p[k] for k in ("capture_interface", "interface_index", "filter", "promiscuous", "flow_schema_version")}, require_addresses=False)
    splits = value["splits"]
    if not isinstance(splits, dict) or set(splits) != {"train", "calibration", "test"}:
        raise ValueError("Three split manifests required")
    all_runs, previous = set(), None
    for name, minimum in (("train", 180), ("calibration", 60), ("test", 60)):
        split = splits[name]
        if set(split) != {"count", "run_ids", "first_start", "last_end", "sha256"} or type(split["count"]) is not int or split["count"] < minimum:
            raise ValueError("Invalid split metadata")
        if not split["run_ids"] or len(set(split["run_ids"])) != len(split["run_ids"]):
            raise ValueError("Distinct run IDs required")
        for run in split["run_ids"]:
            UUID(run)
            all_runs.add(run)
        start, end = aware(split["first_start"]), aware(split["last_end"])
        if end <= start or previous is not None and start < previous:
            raise ValueError("Nonchronological split metadata")
        previous = end
        if not re.fullmatch(r"[0-9a-f]{64}", split["sha256"]):
            raise ValueError("Split digest required")
    if len(all_runs) < 3 or value["sample_count"] != splits["train"]["count"]:
        raise ValueError("Insufficient independent runs/count mismatch")
    if aware(value["trained_at"]) < previous:
        raise ValueError("Model trained before held-out observations existed")
    # No arbitrary packet or nested payload fields in metadata, including evaluation.
    evaluation = value["evaluation"]
    if set(evaluation) != {"calibration_scores", "held_out_scores", "held_out_anomalous", "held_out_count", "reviewed_normal_flag_fraction", "per_run", "limitations"}:
        raise ValueError("Invalid evaluation metadata")
    for key in ("calibration_scores", "held_out_scores"):
        d = evaluation[key]
        if set(d) != {"min", "p50", "p95", "p99", "max"}:
            raise ValueError("Score distribution required")
        numbers = [finite(d[k]) for k in ("min", "p50", "p95", "p99", "max")]
        if numbers != sorted(numbers) or numbers[0] < 0 or numbers[-1] > 1:
            raise ValueError("Invalid score distribution")
    n, k = evaluation["held_out_count"], evaluation["held_out_anomalous"]
    if type(n) is not int or type(k) is not int or n != splits["test"]["count"] or not 0 <= k <= n or not math.isclose(finite(evaluation["reviewed_normal_flag_fraction"]), k / n):
        raise ValueError("Held-out evaluation counts inconsistent")
    if not isinstance(evaluation["per_run"], list) or len(evaluation["per_run"]) != len(splits["test"]["run_ids"]):
        raise ValueError("Per-run evaluation required")
    for run in evaluation["per_run"]:
        if set(run) != {"run_id", "windows", "anomalous", "anomalous_per_observed_hour"} or run["run_id"] not in splits["test"]["run_ids"]:
            raise ValueError("Invalid per-run evaluation")
        if type(run["windows"]) is not int or type(run["anomalous"]) is not int or not 0 <= run["anomalous"] <= run["windows"] or run["windows"] <= 0:
            raise ValueError("Invalid per-run counts")
        if not math.isclose(finite(run["anomalous_per_observed_hour"]), run["anomalous"] * 360 / run["windows"]):
            raise ValueError("Invalid per-hour evaluation")
    if (len({r["run_id"] for r in evaluation["per_run"]}) != len(evaluation["per_run"])
            or sum(r["windows"] for r in evaluation["per_run"]) != n
            or sum(r["anomalous"] for r in evaluation["per_run"]) != k):
        raise ValueError("Per-run counts do not conserve held-out evaluation totals")
    for key in ("score_semantics", "sklearn_version", "numpy_version", "python_version", "joblib_version"):
        if not isinstance(value[key], str) or not 1 <= len(value[key]) <= 200:
            raise ValueError("Missing bounded environment/score metadata")
    if not isinstance(evaluation["limitations"], str) or len(evaluation["limitations"]) > 1000:
        raise ValueError("Bounded evaluation limitations required")
    if finite(value["training_evaluation_seconds"]) < 0 or type(value["rss_after_bytes"]) is not int or value["rss_after_bytes"] < 0:
        raise ValueError("Invalid resource measurements")
    return value


def aware(value):
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timezone-aware timestamps required")
    return result


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Finite numeric measurement required")
    return value


def vector(features):
    if not isinstance(features, dict) or set(features) != set(FEATURE_NAMES):
        raise ValueError("Exactly seven named host-v1 features required; missing is not zero")
    values = [finite(features[name]) for name in FEATURE_NAMES]
    if any(v < 0 for v in values) or any(values[i] > 1 for i in (2, 4, 5)):
        raise ValueError("Feature outside host-v1 bounds")
    if type(values[3]) is not int or values[3] > 10000:
        raise ValueError("Remote peer count must be an integer within the flow cap")
    return values


def context(value, require_addresses=True):
    keys = {"capture_interface", "interface_index", "filter", "promiscuous", "local_addresses", "flow_schema_version"}
    if not require_addresses:
        keys.remove("local_addresses")
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Exact bounded capture context required")
    if value["filter"] != "ip or ip6" or value["promiscuous"] is not False or value["flow_schema_version"] != "phase1b-flow-v1":
        raise ValueError("Incompatible capture profile")
    if not isinstance(value["capture_interface"], str) or not 1 <= len(value["capture_interface"]) <= 255:
        raise ValueError("Selected capture mapping required")
    if type(value["interface_index"]) is not int or value["interface_index"] < 1:
        raise ValueError("Selected interface index required")
    if not require_addresses:
        return
    addresses = value["local_addresses"]
    if not isinstance(addresses, list) or not 1 <= len(addresses) <= 64:
        raise ValueError("Bounded local address context required")
    if addresses != sorted(set(str(ipaddress.ip_address(x)) for x in addresses)):
        raise ValueError("Canonical sorted unique local addresses required")


def eligible(window):
    """Check complete metadata and five reconstructable values; never invent the other two."""
    if (window.get("feature_schema_version") != SCHEMA or window.get("valid") is not True
            or window.get("partial") is not False or window.get("reason") is not None
            or window.get("measurement_source") != "PACKET_METADATA"
            or window.get("kernel_loss") != "unknown"):
        raise ValueError("Only complete valid host-v1 packet windows are eligible")
    values = vector(window.get("features"))
    context(window.get("capture_context"))
    start, end = aware(window["start"]), aware(window["end"])
    if start.timestamp() % 10 or (end - start).total_seconds() != 10:
        raise ValueError("Epoch-aligned ten-second window required")
    if (aware(window["finalized_at"]) - end).total_seconds() < 2 or aware(window["processed_at"]) < aware(window["finalized_at"]):
        raise ValueError("Incomplete finalization")
    names = ("packets", "ip_bytes", "outbound_packets", "inbound_packets", "outbound_bytes", "inbound_bytes",
             "tcp_packets", "udp_packets", "flow_count", "dropped", "unknown_packets", "unknown_bytes", "other_packets")
    for name in names:
        if type(window[name]) is not int or window[name] < 0:
            raise ValueError("Non-negative aggregate integer required: " + name)
    n, b, tcp = window["packets"], window["ip_bytes"], window["tcp_packets"]
    if (any(window[x] for x in ("dropped", "unknown_packets", "unknown_bytes", "other_packets"))
            or n != window["outbound_packets"] + window["inbound_packets"]
            or b != window["outbound_bytes"] + window["inbound_bytes"]
            or n != tcp + window["udp_packets"] or not values[3] <= window["flow_count"] <= min(n, 10000)):
        raise ValueError("Aggregate conservation/completeness failure")
    expected = {0: n / 10, 1: b / 10, 2: window["outbound_bytes"] / b if b else 0,
                5: window["udp_packets"] / n if n else 0, 6: b / n if n else 0}
    if any(not math.isclose(values[i], v, rel_tol=0, abs_tol=1e-12) for i, v in expected.items()):
        raise ValueError("Feature vector conflicts with aggregate metadata")
    if (not n and any(values)) or (n and (not b or not values[3])):
        raise ValueError("Invalid idle/active feature vector")
    for packet_count, byte_count in (("outbound_packets", "outbound_bytes"), ("inbound_packets", "inbound_bytes")):
        if (window[packet_count] == 0) != (window[byte_count] == 0):
            raise ValueError("Directional packets and IP bytes are inconsistent")
    if (not tcp and values[4] != 0) or not math.isclose(values[4] * tcp, round(values[4] * tcp), abs_tol=1e-9, rel_tol=0):
        raise ValueError("SYN fraction must represent an observed integer TCP SYN count")
    return values


def profile(session, window):
    for key in ("source_id", "run_id", "session_id"):
        UUID(str(session[key]))
    if session["mode"] not in MODES or aware(window["start"]) < aware(session["started_at"]):
        raise ValueError("Mode/session coverage mismatch")
    for key in ("session_id", "run_id", "mode", "interface_name"):
        if window[key] != session[key]:
            raise ValueError("Window/session identity mismatch")
    c = window["capture_context"]
    return {key: session[key] for key in ("source_id", "mode", "interface_name", "observation_profile")} | {
        key: c[key] for key in ("capture_interface", "interface_index", "filter", "promiscuous", "flow_schema_version")}
