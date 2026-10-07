"""Versioned local artifacts; loading requires a separately trusted model digest."""
import hashlib
import io
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import tempfile

import joblib
import numpy as np
import sklearn

from sensor.features import FEATURE_NAMES
from .contracts import GENERATOR_VERSION, MODEL_VERSION, MODE, canonical_json, digest

MAX_BUNDLE_BYTES = 32 * 1024 * 1024


def atomic_bytes(path, data):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, prefix=".lab-", suffix=".tmp") as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def environment():
    return {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__, "scipy": version("scipy"), "shap": version("shap")}


def write_artifacts(output_dir, data, bundle, result):
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    names = ("dataset.json", "truth.json", "splits.json", "model.joblib", "result.json", "manifest.json")
    if any((directory / name).exists() for name in names):
        raise ValueError("artifact directory already contains an experiment; choose a new output directory")
    stream = io.BytesIO()
    joblib.dump(bundle, stream, compress=3)
    blob = stream.getvalue()
    if len(blob) > MAX_BUNDLE_BYTES:
        raise ValueError("model artifact exceeds size budget")
    features_only = {key: value for key, value in data.items() if key not in {"truth", "sha256"}}
    payloads = {"dataset.json": canonical_json(features_only), "truth.json": canonical_json(data["truth"]),
                "splits.json": canonical_json(data["splits"]), "model.joblib": blob,
                "result.json": canonical_json(result)}
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    manifest = {"schema_version": MODEL_VERSION, "mode": MODE, "feature_names": list(FEATURE_NAMES),
                "generator_version": GENERATOR_VERSION,
                "dataset_sha256": data["sha256"], "split_sha256": digest(data["splits"]),
                "config_sha256": digest(data["config"]), "environment": environment(), "files": hashes,
                "trust_notice": "Only load a locally generated model whose SHA-256 was obtained independently. An adjacent manifest is not a trust source."}
    for name, content in payloads.items():
        atomic_bytes(directory / name, content)
    atomic_bytes(directory / "manifest.json", canonical_json(manifest))
    return manifest


def load_trusted_bundle(directory, *, expected_sha256):
    """Joblib can execute code. A digest supplied from a trusted run is mandatory."""
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("a separately trusted lowercase SHA-256 is required")
    directory = Path(directory)
    manifest_path, model_path = directory / "manifest.json", directory / "model.joblib"
    if manifest_path.stat().st_size > 64 * 1024 or model_path.stat().st_size > MAX_BUNDLE_BYTES:
        raise ValueError("artifact size budget exceeded")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != MODEL_VERSION or manifest.get("mode") != MODE or
            manifest.get("feature_names") != list(FEATURE_NAMES) or manifest.get("environment") != environment()):
        raise ValueError("incompatible lab manifest or environment; never promote this model to LIVE")
    blob = model_path.read_bytes()
    if len(blob) > MAX_BUNDLE_BYTES or hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise ValueError("model digest does not match separately trusted SHA-256")
    bundle = joblib.load(io.BytesIO(blob))
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    if (not isinstance(bundle, dict) or bundle.get("schema_version") != MODEL_VERSION or bundle.get("mode") != MODE or
            bundle.get("feature_names") != list(FEATURE_NAMES) or
            type(bundle.get("isolation_forest")) is not IsolationForest or
            type(bundle.get("random_forest")) is not RandomForestClassifier or
            type(bundle.get("dummy")) is not DummyClassifier):
        raise ValueError("unsupported lab bundle")
    return bundle
