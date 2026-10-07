"""Dependency-free validation shared by the CLI, worker and HTTP boundary."""
import hashlib
import json
import math

SCHEMA_VERSION = "lab-result-v1"
GENERATOR_VERSION = "metadata-scenarios-v1"
MODEL_VERSION = "lab-model-v1"
MODE = "SIMULATION"
FAMILIES = ("routine", "bulk_transfer", "fanout", "syn_burst", "udp_burst")
BENIGN = frozenset(FAMILIES[:2])
MAX_WINDOWS = 20_000
MAX_EVENTS = 2_000_000
MAX_EVENTS_PER_WINDOW = 512
MAX_RESULT_BYTES = 4 * 1024 * 1024
DEFAULTS = {"seed": 42, "runs_per_family": 10, "windows_per_run": 30,
            "intensity": 1.0, "noise": 0.15, "gap_probability": 0.02}
LIMITS = {"seed": (0, 2147483647, int), "runs_per_family": (6, 30, int),
          "windows_per_run": (12, 120, int), "intensity": (0.5, 2.0, float),
          "noise": (0.0, 1.0, float), "gap_probability": (0.0, 0.15, float)}


class ExperimentCancelled(Exception):
    """The caller explicitly cancelled; no successful result is produced."""


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_config(value):
    if not isinstance(value, dict) or set(value) - set(DEFAULTS):
        raise ValueError("config must contain only supported scenario settings")
    result = DEFAULTS.copy()
    for key, item in value.items():
        lower, upper, kind = LIMITS[key]
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{key} must be a number")
        if kind is int and not isinstance(item, int):
            raise ValueError(f"{key} must be an integer")
        if not lower <= item <= upper or not math.isfinite(item):
            raise ValueError(f"{key} must be between {lower} and {upper}")
        result[key] = kind(item)
    if result["runs_per_family"] * result["windows_per_run"] * len(FAMILIES) > MAX_WINDOWS:
        raise ValueError("window budget exceeded")
    return result


def check_cancel(cancelled):
    if cancelled is not None and cancelled():
        raise ExperimentCancelled("Experiment cancelled")
