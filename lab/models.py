"""Lab-only estimators. Neither model names nor labels enter feature vectors."""
import math
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from sensor.features import FEATURE_NAMES
from .contracts import BENIGN, FAMILIES, MODEL_VERSION, MODE, check_cancel, digest

IF_NAME = "Isolation Forest"
RF_NAME = "Random Forest"
DUMMY_NAME = "Most-frequent baseline"
RULE_NAME = "Heuristic rules"


def vectors(samples):
    """Accept exact numeric feature dictionaries, never an annotated dataset."""
    result = []
    for features in samples:
        if not isinstance(features, dict) or set(features) != set(FEATURE_NAMES):
            raise ValueError("exact host-v1 numeric features required")
        row = []
        for name in FEATURE_NAMES:
            value = features[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1e12 or not math.isfinite(value):
                raise ValueError("features must be finite non-negative numbers")
            if name.endswith("fraction") and value > 1:
                raise ValueError("fraction outside 0..1")
            row.append(float(value))
        result.append(row)
    if not result:
        raise ValueError("at least one complete feature window is required")
    return np.asarray(result, dtype=float)


def partition(data, split):
    run_ids = set(data["splits"][split]["run_ids"])
    return [item for item in data["samples"] if item["run_id"] in run_ids and item["features"] is not None]


def fit_models(data, *, progress=None, cancelled=None, excluded_family=None):
    if excluded_family is not None and excluded_family not in set(FAMILIES) - BENIGN:
        raise ValueError("only a challenge family may be excluded for an unknown-family experiment")
    train, validation = partition(data, "train"), partition(data, "validation")
    if excluded_family is not None:
        excluded_runs = {run["id"] for run in data["runs"] if run["family"] == excluded_family}
        train = [item for item in train if item["run_id"] not in excluded_runs]
    x_train = vectors([item["features"] for item in train])
    y_train = np.asarray([data["truth"][item["id"]]["family"] for item in train])
    benign_train = x_train[np.isin(y_train, list(BENIGN))]
    benign_validation = [item for item in validation if data["truth"][item["id"]]["family"] in BENIGN]
    expected_families = set(FAMILIES) - {excluded_family}
    if len(benign_train) < 20 or len(benign_validation) < 10 or set(y_train) != expected_families:
        raise ValueError("insufficient complete training/calibration coverage")
    iforest = IsolationForest(n_estimators=100, max_samples=min(256, len(benign_train)),
                              contamination="auto", random_state=data["config"]["seed"], n_jobs=1)
    forest = RandomForestClassifier(n_estimators=100, min_samples_leaf=2,
                                    class_weight="balanced", max_depth=12,
                                    random_state=data["config"]["seed"], n_jobs=1)
    dummy = DummyClassifier(strategy="most_frequent")
    for index, (model, x, y) in enumerate(((iforest, benign_train, None), (forest, x_train, y_train), (dummy, x_train, y_train))):
        check_cancel(cancelled)
        if progress:
            progress("fitting_isolation_forest" if index == 0 else "fitting_random_forest" if index == 1 else "fitting_baseline")
        model.fit(x, y)
    check_cancel(cancelled)
    calibration = -iforest.score_samples(vectors([item["features"] for item in benign_validation]))
    threshold = float(np.quantile(calibration, 0.99, method="linear"))
    quantiles = np.quantile(benign_train, [0.5, 0.05, 0.95, 0.99], axis=0)
    references = {name: dict(zip(("median", "p05", "p95", "p99"), map(float, quantiles[:, index])))
                  for index, name in enumerate(FEATURE_NAMES)}
    # These are deliberately simple, fixed comparator rules. They are not ML
    # predictions and have not been selected/tuned against the test partition.
    rule_parameters = {"udp_fraction": 0.7, "tcp_syn_fraction": 0.55,
                       "unique_remote_peers": 18, "ip_bytes_per_second": 9000}
    rng = np.random.default_rng(data["config"]["seed"])
    background = x_train[rng.choice(len(x_train), min(64, len(x_train)), replace=False)]
    return {"schema_version": MODEL_VERSION, "mode": MODE, "feature_names": list(FEATURE_NAMES),
            "isolation_forest": iforest, "random_forest": forest, "dummy": dummy,
            "threshold": threshold, "references": references, "rule_parameters": rule_parameters,
            "shap_background": background, "dataset_sha256": data["sha256"],
            "excluded_family": excluded_family, "training_families": sorted(expected_families),
            "training_run_ids": sorted({item["run_id"] for item in train}),
            "calibration_run_ids": sorted({item["run_id"] for item in benign_validation}),
            "split_sha256": digest(data["splits"]), "config_sha256": digest(data["config"]),
            "training_windows": len(train), "benign_training_windows": len(benign_train),
            "calibration_windows": len(benign_validation)}


def rule_predict(x, parameters):
    result = []
    for row in x:
        features = dict(zip(FEATURE_NAMES, row))
        if features["udp_fraction"] >= parameters["udp_fraction"]:
            result.append("udp_burst")
        elif features["tcp_syn_fraction"] >= parameters["tcp_syn_fraction"]:
            result.append("syn_burst")
        elif features["unique_remote_peers"] >= parameters["unique_remote_peers"]:
            result.append("fanout")
        elif features["ip_bytes_per_second"] >= parameters["ip_bytes_per_second"]:
            result.append("bulk_transfer")
        else:
            result.append("routine")
    return np.asarray(result)


def predict_features(bundle, features):
    if bundle.get("schema_version") != MODEL_VERSION or bundle.get("mode") != MODE:
        raise ValueError("only a lab SIMULATION bundle is supported")
    x = vectors(features)
    probabilities = bundle["random_forest"].predict_proba(x)
    return {"random_forest": bundle["random_forest"].classes_[np.argmax(probabilities, axis=1)],
            "class_probability": np.max(probabilities, axis=1),
            "dummy": bundle["dummy"].predict(x), "rules": rule_predict(x, bundle["rule_parameters"]),
            "anomaly_score": -bundle["isolation_forest"].score_samples(x)}


def model_descriptions(bundle):
    return [{"name": name, "task": task, "parameters": model.get_params(), "training_windows": count}
            for name, task, model, count in (
                (IF_NAME, "benign-distribution deviation", bundle["isolation_forest"], bundle["benign_training_windows"]),
                (RF_NAME, "injected traffic-behaviour family", bundle["random_forest"], bundle["training_windows"]),
                (DUMMY_NAME, "most frequent training family", bundle["dummy"], bundle["training_windows"]))] + [
            {"name": RULE_NAME, "task": "fixed heuristic family comparator; not learned",
             "parameters": bundle["rule_parameters"], "training_windows": 0}]
