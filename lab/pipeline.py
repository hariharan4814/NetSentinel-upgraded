"""Independent reproducible experiment: generated metadata to evaluated models."""
from datetime import datetime, timezone
import threading
import time

import numpy as np
import psutil

from sensor.features import FEATURE_NAMES
from .artifacts import write_artifacts
from .contracts import (FAMILIES, MAX_RESULT_BYTES, MODE, SCHEMA_VERSION,
                        canonical_json, check_cancel, validate_config)
from .explanations import explain_windows
from .metrics import anomaly_metrics, classification_metrics
from .models import (DUMMY_NAME, RF_NAME, RULE_NAME, fit_models,
                     model_descriptions, partition, predict_features)
from .simulation import generate_dataset


class MemorySampler:
    """Sample this process, not whole-machine use; very short peaks may be missed."""
    def __init__(self):
        self.peak = 0
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        process = psutil.Process()
        while True:
            self.peak = max(self.peak, process.memory_info().rss)
            if self.stop.wait(0.025):
                break

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()


def evaluate_dataset(data, bundle, *, progress=None, cancelled=None):
    test = partition(data, "test")
    if not test:
        raise ValueError("no complete test windows")
    check_cancel(cancelled)
    if progress:
        progress("evaluating", 0, len(test))
    predictions = predict_features(bundle, [item["features"] for item in test])
    actual = [data["truth"][item["id"]]["family"] for item in test]
    classification = [classification_metrics(name, actual, predictions[key], FAMILIES)
                      for name, key in ((RF_NAME, "random_forest"), (DUMMY_NAME, "dummy"), (RULE_NAME, "rules"))]
    test_ids = set(data["splits"]["test"]["run_ids"])
    all_test = [item for item in data["samples"] if item["run_id"] in test_ids]
    anomaly = anomaly_metrics([data["truth"][item["id"]]["challenge"] for item in test],
                              predictions["anomaly_score"], bundle["threshold"],
                              unscored_windows=len(all_test) - len(test))
    by_id = {item["id"]: index for index, item in enumerate(test)}
    timeline = []
    # 2,000 presentation windows keep the API/report bounded; metrics use all.
    for item in all_test[:2000]:
        check_cancel(cancelled)
        index = by_id.get(item["id"])
        scored = index is not None
        score = float(predictions["anomaly_score"][index]) if scored else None
        timeline.append({key: item[key] for key in ("id", "run_id", "window_index", "time_seconds", "features")} |
                        {"truth_family": data["truth"][item["id"]]["family"],
                         "challenge": data["truth"][item["id"]]["challenge"],
                         "predicted_family": str(predictions["random_forest"][index]) if scored else None,
                         "class_probability": float(predictions["class_probability"][index]) if scored else None,
                         "anomaly_score": score, "anomalous": bool(score > bundle["threshold"]) if scored else None})
    durations = []
    # Measure full single-window inference, not a batched-time/n estimate.
    for item in test[:min(24, len(test))]:
        check_cancel(cancelled)
        started = time.perf_counter()
        predict_features(bundle, [item["features"]])
        durations.append((time.perf_counter() - started) * 1000)
    if progress:
        progress("evaluating", len(test), len(test))
    selected, seen = [], set()
    for item in timeline:
        family = item["predicted_family"]
        if item["features"] is not None and family not in seen:
            selected.append(item)
            seen.add(family)
    for item in sorted((row for row in timeline if row["anomaly_score"] is not None),
                       key=lambda row: row["anomaly_score"], reverse=True):
        if len(selected) >= 8:
            break
        if item not in selected:
            selected.append(item)
    if progress:
        progress("explaining", 0, len(selected))
    explanations, warnings = explain_windows(bundle, selected, cancelled=cancelled)
    if progress:
        progress("explaining", len(selected), len(selected))
    return {"classification": classification, "anomaly": anomaly, "timeline": timeline,
            "explanations": explanations, "warnings": warnings,
            "displayed_windows": len(timeline), "total_test_windows": len(all_test),
            "inference_p50_ms": float(np.quantile(durations, 0.5)),
            "inference_p95_ms": float(np.quantile(durations, 0.95))}


def run_experiment(config, *, output_dir=None, progress=None, cancelled=None):
    config = validate_config(config)
    started = time.perf_counter()
    with MemorySampler() as memory:
        check_cancel(cancelled)
        data = generate_dataset(config, progress=progress, cancelled=cancelled)
        generated = time.perf_counter()
        bundle = fit_models(data, progress=progress, cancelled=cancelled)
        trained = time.perf_counter()
        evaluation = evaluate_dataset(data, bundle, progress=progress, cancelled=cancelled)
        evaluated = time.perf_counter()
        valid = sum(item["features"] is not None for item in data["samples"])
        result = {"schema_version": SCHEMA_VERSION, "mode": MODE,
                  "generated_at": datetime.now(timezone.utc).isoformat(), "config": config,
                  "dataset": {"sha256": data["sha256"], "total_windows": len(data["samples"]),
                              "valid_windows": valid, "unscored_windows": len(data["samples"]) - valid,
                              "event_count": data["event_count"], "feature_names": list(FEATURE_NAMES),
                              "splits": data["splits"]},
                  "models": model_descriptions(bundle), "references": bundle["references"],
                  **{key: evaluation[key] for key in ("classification", "anomaly", "timeline", "explanations",
                                                     "displayed_windows", "total_test_windows")},
                  "performance": {"generation_seconds": generated - started,
                                  "training_seconds": trained - generated,
                                  "evaluation_seconds": evaluated - trained,
                                  "total_seconds": evaluated - started,
                                  "inference_p50_ms": evaluation["inference_p50_ms"],
                                  "inference_p95_ms": evaluation["inference_p95_ms"],
                                  "peak_rss_bytes": memory.peak},
                  "limitations": [
                      "SIMULATION only: generated metadata, no packets sent or real attacks observed. No LIVE model promotion.",
                      "Challenge labels describe injected traffic families, not malware or hostile intent. Noise intentionally creates overlapping feature distributions.",
                      "Held-out whole runs use new seeds but the same generator families; this is not external-network generalization or unknown-attack detection evidence.",
                      "Isolation Forest fits benign training windows; negative score_samples above benign validation p99 is anomalous, not an attack probability.",
                      "Random Forest class probabilities are uncalibrated family outputs, not confidence of compromise. Rules are fixed heuristic comparators.",
                      "References are learned from benign training only; SHAP uses all-family training background and explains model output, not real-world causation. The per-case method identifies TreeSHAP or bounded exact enumeration after an independent output check.",
                      "Missing observations are unscored and excluded from metrics. False alerts/hour uses complete benign virtual ten-second windows.",
                      "All held-out test windows contribute to metrics; replay is capped at the first 2,000 windows. Test prevalence is controlled by the generator, not representative of production.",
                      "Peak memory is this process RSS sampled every 25ms, including imports; short peaks may be missed. Inference latency samples the first 24 valid test windows; it is not end-to-end UI latency.",
                      "This single experiment does not establish uncertainty or unknown-family performance. The separate benchmark CLI supports repeated seeds, conditional run bootstrap and excluded-family stress tests; drift, external data and ablations remain future checks.",
                  ] + evaluation["warnings"]}
        check_cancel(cancelled)
        if len(canonical_json(result)) > MAX_RESULT_BYTES:
            raise ValueError("result exceeds 4 MiB presentation budget")
        if output_dir is not None:
            if progress:
                progress("saving")
            write_artifacts(output_dir, data, bundle, result)
        check_cancel(cancelled)
        if progress:
            progress("complete", 1, 1)
        return result
