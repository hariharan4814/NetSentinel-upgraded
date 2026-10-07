"""Bounded JSON contract validation without importing the training runtime."""
from datetime import datetime
import math
import re
from rest_framework.exceptions import ValidationError
from lab.contracts import validate_config, canonical_json, MAX_RESULT_BYTES, FAMILIES

FEATURES = ("packets_per_second", "ip_bytes_per_second", "outbound_byte_fraction",
            "unique_remote_peers", "tcp_syn_fraction", "udp_fraction", "mean_ip_packet_bytes")


def fail(message="Invalid experiment request."):
    raise ValidationError(message)


def keys(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        fail("Object has missing or unsupported fields.")


def number(value, low=0, high=1e15, nullable=False, integer=False):
    if value is None and nullable:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail("Expected a finite number.")
    if (integer and not isinstance(value, int)) or not low <= value <= high:
        fail("Number outside the supported range.")
    if not math.isfinite(value):
        fail("Expected a finite number.")


def text(value, maximum=200):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 for c in value):
        fail("Invalid bounded text.")


def sequence(value, maximum=20000):
    if not isinstance(value, list) or len(value) > maximum:
        fail("Invalid or oversized list.")


def config(value):
    try:
        return validate_config(value)
    except ValueError as exc:
        fail(str(exc))


def lease(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        fail("Invalid worker lease.")


def finite_tree(value, depth=0):
    if depth > 20:
        fail("Result nesting exceeds the limit.")
    if isinstance(value, dict):
        if len(value) > 100:
            fail("Too many object fields.")
        for key, child in value.items():
            text(key, 100)
            finite_tree(child, depth + 1)
    elif isinstance(value, list):
        sequence(value)
        for child in value:
            finite_tree(child, depth + 1)
    elif isinstance(value, str):
        text(value, 2000)
    elif value is None or isinstance(value, bool):
        pass
    elif isinstance(value, (int, float)):
        number(value, -1e18, 1e18)
    else:
        fail()


def result(value):
    """Validate provenance, required shapes, finite metrics and display bounds.

    This is not a claim that an authenticated worker's scientific conclusions
    are trustworthy: reproducibility and calibration are tested in lab.pipeline.
    """
    required = ("schema_version", "mode", "generated_at", "config", "dataset", "models",
                "references", "classification", "anomaly", "timeline", "explanations",
                "performance", "limitations", "displayed_windows", "total_test_windows")
    keys(value, required, ("rigor", "versions", "artifacts", "explanation_status", "reproducibility"))
    finite_tree(value)
    if len(canonical_json(value)) > MAX_RESULT_BYTES - 1024:
        fail("Result exceeds the bounded finish envelope.")
    if value["schema_version"] != "lab-result-v1" or value["mode"] != "SIMULATION":
        fail("Only versioned SIMULATION lab results are accepted.")
    try:
        stamp = datetime.fromisoformat(value["generated_at"].replace("Z", "+00:00"))
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            fail("Result timestamp must be UTC.")
    except (ValueError, TypeError, AttributeError):
        fail("Invalid generation timestamp.")
    if config(value["config"]) != value["config"]:
        fail("Result config must contain normalized settings.")
    dataset = value["dataset"]
    keys(dataset, ("sha256", "total_windows", "valid_windows", "unscored_windows", "event_count", "feature_names", "splits"))
    if not isinstance(dataset["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", dataset["sha256"]):
        fail("Invalid dataset digest.")
    for name in ("total_windows", "valid_windows", "unscored_windows"):
        number(dataset[name], 0, 20000, integer=True)
    number(dataset["event_count"], 0, 2000000, integer=True)
    if dataset["valid_windows"] + dataset["unscored_windows"] != dataset["total_windows"]:
        fail("Dataset coverage does not reconcile.")
    if dataset["feature_names"] != list(FEATURES):
        fail("Unsupported lab feature contract.")
    keys(dataset["splits"], ("train", "validation", "test"))
    seen = set()
    split_windows = 0
    for split in dataset["splits"].values():
        keys(split, ("run_ids", "windows"))
        sequence(split["run_ids"], 150)
        for run_id in split["run_ids"]:
            text(run_id, 100)
            if run_id in seen:
                fail("Runs cannot cross evaluation splits.")
            seen.add(run_id)
        number(split["windows"], 0, 20000, integer=True)
        split_windows += split["windows"]
    if split_windows != dataset["total_windows"]:
        fail("Split counts do not reconcile.")
    sequence(value["models"], 10)
    for model in value["models"]:
        keys(model, ("name", "task", "parameters", "training_windows"))
        text(model["name"], 80)
        text(model["task"], 100)
        if not isinstance(model["parameters"], dict):
            fail()
        number(model["training_windows"], 0, 20000, integer=True)
    keys(value["references"], FEATURES)
    for reference in value["references"].values():
        keys(reference, ("median", "p05", "p95", "p99"))
        for item in reference.values():
            number(item)
        if not reference["p05"] <= reference["median"] <= reference["p95"] <= reference["p99"]:
            fail("Reference percentiles must be ordered.")
    sequence(value["classification"], 10)
    for evaluation in value["classification"]:
        keys(evaluation, ("model", "labels", "confusion_matrix", "accuracy", "balanced_accuracy", "macro_f1", "per_class"))
        text(evaluation["model"], 80)
        if evaluation["labels"] != list(FAMILIES):
            fail("Unsupported classification labels.")
        matrix = evaluation["confusion_matrix"]
        if not isinstance(matrix, list) or len(matrix) != len(FAMILIES):
            fail("Confusion matrix shape is invalid.")
        for row in matrix:
            if not isinstance(row, list) or len(row) != len(FAMILIES):
                fail("Confusion matrix shape is invalid.")
            for count in row:
                number(count, 0, 20000, integer=True)
        for name in ("accuracy", "balanced_accuracy", "macro_f1"):
            number(evaluation[name], 0, 1, nullable=True)
        if not isinstance(evaluation["per_class"], list) or len(evaluation["per_class"]) != len(FAMILIES):
            fail()
        for entry in evaluation["per_class"]:
            keys(entry, ("label", "precision", "recall", "f1", "support"))
            if entry["label"] not in FAMILIES:
                fail()
            for name in ("precision", "recall", "f1"):
                number(entry[name], 0, 1, nullable=True)
            number(entry["support"], 0, 20000, integer=True)
    keys(value["anomaly"], ("threshold", "precision", "recall", "false_positive_rate", "average_precision", "false_alerts_per_hour", "scored_windows", "unscored_windows"))
    for name in ("precision", "recall", "false_positive_rate", "average_precision"):
        number(value["anomaly"][name], 0, 1, nullable=True)
    for name in ("threshold", "false_alerts_per_hour"):
        number(value["anomaly"][name], nullable=True)
    for name in ("scored_windows", "unscored_windows"):
        number(value["anomaly"][name], 0, 20000, integer=True)
    for name in ("displayed_windows", "total_test_windows"):
        number(value[name], 0, 20000, integer=True)
    sequence(value["timeline"])
    if not len(value["timeline"]) == value["displayed_windows"] <= value["total_test_windows"] == dataset["splits"]["test"]["windows"]:
        fail("Timeline display counts do not reconcile.")
    for window in value["timeline"]:
        keys(window, ("id", "run_id", "window_index", "time_seconds", "truth_family", "challenge", "features", "predicted_family", "class_probability", "anomaly_score", "anomalous"))
        text(window["id"], 100)
        if window["run_id"] not in dataset["splits"]["test"]["run_ids"]:
            fail("Timeline must use held-out runs.")
        if window["truth_family"] not in FAMILIES or type(window["challenge"]) is not bool:
            fail()
        if window["predicted_family"] not in (*FAMILIES, None) or (window["anomalous"] is not None and type(window["anomalous"]) is not bool):
            fail()
        number(window["window_index"], 0, 120, integer=True)
        number(window["time_seconds"])
        number(window["class_probability"], 0, 1, nullable=True)
        number(window["anomaly_score"], nullable=True)
        if window["features"] is not None:
            keys(window["features"], FEATURES)
            for item in window["features"].values():
                number(item)
        elif any(window[key] is not None for key in ("predicted_family", "class_probability", "anomaly_score", "anomalous")):
            fail("Missing observations must stay unscored.")
    sequence(value["explanations"], 100)
    for explanation in value["explanations"]:
        keys(explanation, ("window_id", "method", "predicted_family", "base_value", "output_value", "additivity_error", "features"))
        text(explanation["window_id"], 100)
        text(explanation["method"], 200)
        if explanation["predicted_family"] not in FAMILIES:
            fail()
        for name in ("base_value", "output_value", "additivity_error"):
            number(explanation[name], -1e15, 1e15, nullable=True)
        sequence(explanation["features"], len(FEATURES))
        for entry in explanation["features"]:
            keys(entry, ("feature", "value", "reference_p95", "contribution"))
            if entry["feature"] not in FEATURES:
                fail()
            for name in ("value", "reference_p95", "contribution"):
                number(entry[name], -1e15, 1e15, nullable=True)
    keys(value["performance"], ("generation_seconds", "training_seconds", "evaluation_seconds", "total_seconds", "inference_p50_ms", "inference_p95_ms", "peak_rss_bytes"))
    for item in value["performance"].values():
        number(item, nullable=True)
    sequence(value["limitations"], 100)
    for item in value["limitations"]:
        text(item, 2000)
    return value
