"""Optional bounded research study; never changes the web experiment protocol."""
from collections import Counter
import time

import numpy as np

from .contracts import BENIGN, FAMILIES, MODE, check_cancel, validate_config
from .metrics import anomaly_metrics, classification_metrics
from .models import DUMMY_NAME, RF_NAME, RULE_NAME, fit_models, partition, predict_features
from .simulation import generate_dataset


def group_bootstrap(actual, predicted, run_ids, *, seed, repetitions=200):
    """Resample whole test runs, keeping a fitted model fixed (conditional CI)."""
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or not 50 <= repetitions <= 1000:
        raise ValueError("bootstrap repetitions must be an integer between 50 and 1000")
    if not (len(actual) == len(predicted) == len(run_ids)):
        raise ValueError("bootstrap arrays must have matching lengths")
    groups = sorted(set(run_ids))
    if len(groups) < 2:
        return {"lower": None, "upper": None, "repetitions": 0, "unit": "whole held-out run"}
    indices = {group: [i for i, value in enumerate(run_ids) if value == group] for group in groups}
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repetitions):
        chosen = [index for group in rng.choice(groups, len(groups), replace=True) for index in indices[group]]
        values.append(classification_metrics("bootstrap", [actual[i] for i in chosen],
                                            [predicted[i] for i in chosen], FAMILIES)["macro_f1"])
    return {"lower": float(np.quantile(values, .025)), "upper": float(np.quantile(values, .975)),
            "repetitions": repetitions, "unit": "whole held-out run",
            "interpretation": "95% percentile interval conditional on this fitted model; absent-family F1 is zero"}


def run_benchmark(config, *, seeds=(42, 43, 44), excluded_family="fanout",
                  repetitions=200, progress=None, cancelled=None):
    """Compare repeated independent seeds plus an excluded-training-family stress test."""
    config = validate_config(config)
    if (not isinstance(seeds, (tuple, list)) or not 2 <= len(seeds) <= 5 or
            any(isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647 for seed in seeds) or
            len(set(seeds)) != len(seeds)):
        raise ValueError("supply two to five distinct integer seeds in 0..2147483647")
    if excluded_family not in set(FAMILIES) - BENIGN:
        raise ValueError("excluded family must be a challenge family")
    # Reject excessive work before generation/fitting.
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 50 <= repetitions <= 1000:
        raise ValueError("bootstrap repetitions must be an integer between 50 and 1000")
    started = time.perf_counter()
    runs = []
    for seed in seeds:
        check_cancel(cancelled)
        if progress:
            progress("benchmark_seed", len(runs), len(seeds))
        data = generate_dataset({**config, "seed": seed}, cancelled=cancelled)
        bundle = fit_models(data, cancelled=cancelled)
        test = partition(data, "test")
        features = [item["features"] for item in test]
        actual = [data["truth"][item["id"]]["family"] for item in test]
        challenge = [data["truth"][item["id"]]["challenge"] for item in test]
        predictions = predict_features(bundle, features)
        metrics = []
        for name, key in ((RF_NAME, "random_forest"), (DUMMY_NAME, "dummy"), (RULE_NAME, "rules")):
            check_cancel(cancelled)
            row = classification_metrics(name, actual, predictions[key], FAMILIES)
            row["macro_f1_group_bootstrap"] = group_bootstrap(actual, predictions[key],
                [item["run_id"] for item in test], seed=seed, repetitions=repetitions)
            metrics.append(row)
        # Same split and numeric features; the selected challenge label is removed
        # from all supervised training and SHAP background, never reassigned benign.
        unknown_bundle = fit_models(data, excluded_family=excluded_family, cancelled=cancelled)
        unknown_indices = [index for index, label in enumerate(actual) if label == excluded_family]
        unknown = predict_features(unknown_bundle, [features[index] for index in unknown_indices])
        detection_rate = float(np.mean(unknown["anomaly_score"] > unknown_bundle["threshold"]))
        unknown_result = {"excluded_family": excluded_family,
            "trained_classes": unknown_bundle["random_forest"].classes_.tolist(),
            "scored_windows": len(unknown_indices), "isolation_forest_flagged_fraction": detection_rate,
            "forced_known_predictions": dict(Counter(map(str, unknown["random_forest"]))),
            "interpretation": "Closed-set classifier cannot name the excluded family. Flagged fraction is generated-pattern deviation, not unknown-attack accuracy."}
        runs.append({"seed": seed, "dataset_sha256": data["sha256"], "splits": data["splits"],
                     "classification": metrics,
                     "anomaly": anomaly_metrics(challenge, predictions["anomaly_score"], bundle["threshold"],
                         unscored_windows=data["splits"]["test"]["windows"] - len(test)),
                     "unknown_family": unknown_result})
    summary = []
    for index in range(3):
        values = [row["classification"][index]["macro_f1"] for row in runs]
        summary.append({"model": runs[0]["classification"][index]["model"],
                        "macro_f1_mean": float(np.mean(values)), "macro_f1_sample_std": float(np.std(values, ddof=1)),
                        "macro_f1_min": min(values), "macro_f1_max": max(values)})
    check_cancel(cancelled)
    if progress:
        progress("benchmark_complete", len(seeds), len(seeds))
    return {"schema_version": "lab-benchmark-v1", "mode": MODE, "config": config,
            "seeds": list(seeds), "runs": runs, "summary": summary,
            "seconds": time.perf_counter() - started,
            "limitations": ["All results come from this metadata generator, not a real network or external dataset.",
                "Whole-run bootstrap resamples test groups without refitting; it does not quantify training uncertainty. Repeated-seed dispersion is reported separately.",
                "Few independent runs/seeds yield unstable uncertainty estimates; intervals are exploratory, not proof of generalization.",
                "Unknown-family stress test excludes one challenge family from supervised training; the generator and fixed heuristic rules already encode the family.",
                "Isolation Forest always trains on benign only. Unknown-family flag rate is not a new supervised open-set detector.",
                "Temporal drift, feature ablation and independent external-dataset validation remain unimplemented."]}
