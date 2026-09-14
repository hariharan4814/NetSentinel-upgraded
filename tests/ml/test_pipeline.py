"""Synthetic IN-MEMORY SIMULATION fixtures test software, never LIVE acceptance."""
import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from sensor.features import FEATURE_NAMES as SENSOR_NAMES, host_features
from sensor.flows import Flow, Window
from backend.detection.contract import FEATURE_NAMES, eligible, vector, validate_manifest
from ml.exporter import convert, export
from ml.pipeline import validate, train, load, score, digest, write_json, read_json
from ml.__main__ import publish


def evidence(index=0, run=0):
    start = 1720000000 + run * 86400 + index * 10
    sid, rid = str(UUID(int=run + 1)), str(UUID(int=run + 100))
    packets = 2 + index % 11
    flow = Flow(packets=packets, ip_bytes=packets * (60 + index % 17), outbound_packets=packets,
                outbound_bytes=packets * (60 + index % 17), tcp_syn_packets=1,
                first_observed=start + 1, last_observed=start + 2, min_ip_bytes=60 + index % 17, max_ip_bytes=60 + index % 17)
    key = ("fixture", "TCP", ("192.0.2.1", 1234), ("198.51.100.2", 443))
    w = Window(start=start, mode="SIMULATION", session_id=sid, interface="fixture", flows={key: flow}, finalized_at=start + 12)
    record = {"type": "window", "schema_version": "phase1b-flow-v1", "mode": "SIMULATION", "session_id": sid, "run_id": rid,
              "interface": "fixture", "measurement_source": "PACKET_METADATA", "start": start, "end": start + 10,
              "finalized_at": start + 12, "processed_at": start + 12.1, "partial": False, "dropped": 0,
              "kernel_loss": "unknown", "feature_schema_version": "host-v1", "features": host_features(w, ["192.0.2.1"]),
              "local_addresses": ["192.0.2.1"], "flows": [{"protocol": "TCP", "endpoint_a": key[2], "endpoint_b": key[3], **asdict(flow)}]}
    event = {"type": "capture_started", "schema_version": "phase1b-capture-v1", "mode": "SIMULATION", "session_id": sid, "run_id": rid,
             "interface": "fixture", "capture_interface": "fixture-guid", "interface_index": 1, "observed_at": 1720000000 + run * 86400,
             "kernel_loss": "unknown", "filter": "ip or ip6", "promiscuous": False}
    return record, event


def row(index=0, run=0):
    r, e = evidence(index, run)
    return convert(r, e, str(UUID(int=999)), "test-fixture")


def dataset():
    return {"schema": "netsentinel-dataset-v1", "feature_order": list(FEATURE_NAMES),
            "rows": [row(i, run) for run in range(5) for i in range(100)]}


def review(data):
    return {"dataset_sha256": digest(data), "reviewed_normal": True, "reviewer": "automated-SIMULATION-test-only",
            "notes": "Synthetic unit-test fixture; not genuine LIVE baseline evidence.",
            "run_ids": sorted({r["session"]["run_id"] for r in data["rows"]})}


class ContractTests(unittest.TestCase):
    def test_exact_order_and_hand_calculation(self):
        self.assertEqual(FEATURE_NAMES, SENSOR_NAMES)
        self.assertEqual(eligible(row()["window"]), [.2, 12, 1, 1, .5, 0, 60])

    def test_missing_extra_non_numeric_nonfinite(self):
        for value in (None, "1", True, float("nan"), float("inf"), -1):
            with self.subTest(value=value):
                features = row()["window"]["features"]
                features[FEATURE_NAMES[0]] = value
                with self.assertRaises(ValueError):
                    vector(features)
        f = row()["window"]["features"]
        del f[FEATURE_NAMES[4]]
        with self.assertRaises(ValueError):
            vector(f)

    def test_legacy_partial_invalid_schema_rejected(self):
        for changes in ({"partial": True}, {"valid": False}, {"features": None}, {"feature_schema_version": "wrong"}, {"capture_context": None}, {"reason": "loss"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                eligible(row()["window"] | changes)

    def test_provenance_separation(self):
        data = dataset()
        with self.assertRaisesRegex(ValueError, "mixed"):
            validate(data, review(data))
        data["rows"][0]["session"]["mode"] = "REPLAY"
        data["rows"][0]["window"]["mode"] = "REPLAY"
        with self.assertRaises(ValueError):
            validate(data, review(data), "SIMULATION")

    def test_insufficient_samples_and_review(self):
        data = dataset()
        with self.assertRaises(ValueError):
            validate(data, review(data) | {"reviewed_normal": False}, "SIMULATION")
        data["rows"] = data["rows"][:10]
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            validate(data, review(data), "SIMULATION")

    def test_split_is_whole_run_chronological(self):
        data = dataset()
        splits = validate(data, review(data), "SIMULATION")
        self.assertEqual({k: len(v) for k, v in splits.items()}, {"train": 180, "calibration": 60, "test": 60})

    def test_peers_not_flow_count_and_syn_not_invented(self):
        r, e = evidence()
        second = copy.deepcopy(r["flows"][0])
        second["endpoint_a"] = ("192.0.2.1", 1235)
        r["flows"].append(second)
        r["features"].update(packets_per_second=.4, ip_bytes_per_second=24)
        result = convert(r, e, str(UUID(int=999)), "fixture")
        self.assertEqual(result["window"]["flow_count"], 2)
        self.assertEqual(result["window"]["features"]["unique_remote_peers"], 1)
        del r["flows"][0]["tcp_syn_packets"]
        with self.assertRaises(ValueError):
            convert(r, e, str(UUID(int=999)), "fixture")

    def test_fabricated_supplied_features_rejected(self):
        r, e = evidence()
        r["features"]["tcp_syn_fraction"] = 0
        with self.assertRaises(ValueError):
            convert(r, e, str(UUID(int=999)), "fixture")

    def test_export_encoding_exclusions_and_no_payload(self):
        r, e = evidence()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text('\n'.join(json.dumps(x) for x in (e, r, r | {"partial": True})), encoding="utf-16")
            result = export([path], str(UUID(int=999)), "fixture", "SIMULATION")
            self.assertEqual(result["export"]["eligible"], 1)
            self.assertEqual(sum(result["export"]["excluded"].values()), 1)
            self.assertNotIn("flows", result["rows"][0]["window"])
            self.assertFalse(result["export"]["reviewed_normal"])

    def test_npcap_device_path_interface_canonicalization(self):
        r, e = evidence()
        # Realistic Windows live pattern: start event records alias + Npcap GUID; sniffer records Npcap GUID
        e["interface"] = "Ethernet 3"
        e["capture_interface"] = r"\Device\NPF_{F6428BE8-4357-41F9-A78D-5909098A0567}"
        r["interface"] = r"\Device\NPF_{F6428BE8-4357-41F9-A78D-5909098A0567}"
        res = convert(r, e, str(UUID(int=999)), "ethernet3-standard")
        self.assertEqual(res["session"]["interface_name"], "Ethernet 3")
        self.assertEqual(res["window"]["interface_name"], "Ethernet 3")
        self.assertEqual(res["window"]["capture_context"]["capture_interface"], r"\Device\NPF_{F6428BE8-4357-41F9-A78D-5909098A0567}")
        # Genuinely mismatched interface must be strictly rejected
        r["interface"] = r"\Device\NPF_{OTHER_DEVICE_PATH}"
        with self.assertRaises(ValueError):
            convert(r, e, str(UUID(int=999)), "ethernet3-standard")
        # Genuinely mismatched session/run/mode must also be strictly rejected
        r["interface"] = e["capture_interface"]
        for key, val in (("session_id", str(UUID(int=9999))), ("run_id", str(UUID(int=8888))), ("mode", "REPLAY")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                convert(r | {key: val}, e, str(UUID(int=999)), "ethernet3-standard")


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = dataset()
        cls.directory = Path(cls.temp.name) / "model"
        cls.manifest = train(cls.data, review(cls.data), cls.directory, "SIMULATION")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_manifest_complete(self):
        self.assertEqual(validate_manifest(self.manifest), self.manifest)
        self.assertEqual(self.manifest["sample_count"], 180)
        self.assertEqual(self.manifest["profile"]["mode"], "SIMULATION")

    def test_deterministic_training(self):
        other = Path(self.temp.name) / "second"
        manifest = train(self.data, review(self.data), other, "SIMULATION")
        self.assertEqual(manifest["threshold"], self.manifest["threshold"])
        self.assertEqual(manifest["evaluation"], self.manifest["evaluation"])

    def test_score_generation_vocabulary(self):
        result = score(self.data, self.directory, self.manifest["artifact_sha256"])
        self.assertEqual(len(result["results"]), 500)
        self.assertTrue({r["label"] for r in result["results"]} <= {"NORMAL", "ANOMALOUS"})
        self.assertTrue(all(0 <= r["anomaly_score"] <= 1 for r in result["results"]))

    def test_score_orientation_and_outlier_behavior(self):
        import numpy as np
        estimator, manifest = load(self.directory, self.manifest["artifact_sha256"])
        # Score is defined as negative score_samples: higher means more anomalous
        self.assertIn("negative_score_samples; higher means more unusual", manifest["score_semantics"])
        inlier_vector = np.array([[.7, 46.0, 1.0, 1, .2, 0.0, 67.0]])
        outlier_vector = np.array([[100.0, 50000.0, 1.0, 50, 1.0, 0.5, 1400.0]])
        raw_inlier = estimator.score_samples(inlier_vector)[0]
        raw_outlier = estimator.score_samples(outlier_vector)[0]
        score_inlier = -raw_inlier
        score_outlier = -raw_outlier
        self.assertGreater(score_outlier, score_inlier)
        self.assertLess(raw_outlier, raw_inlier)

    def test_schema_order_missing_manifest(self):
        for change in ({"schema": "wrong"}, {"feature_schema_version": "wrong"}, {"feature_order": list(reversed(FEATURE_NAMES))}):
            with self.assertRaises(ValueError):
                validate_manifest(self.manifest | change)
        bad = dict(self.manifest)
        del bad["trained_at"]
        with self.assertRaises(ValueError):
            validate_manifest(bad)

    def test_bad_digest_rejected_before_load(self):
        with self.assertRaisesRegex(ValueError, "digest"):
            load(self.directory, "0" * 64)

    def test_malformed_artifact_rejected(self):
        directory = Path(self.temp.name) / "malformed"
        directory.mkdir()
        content = b"not a model artifact"
        (directory / "model.joblib").write_bytes(content)
        trusted = hashlib.sha256(content).hexdigest()
        write_json(directory / "manifest.json", self.manifest | {"artifact_sha256": trusted})
        with self.assertRaisesRegex(ValueError, "Malformed"):
            load(directory, trusted)

    def test_manifest_tampering_rejected(self):
        directory = Path(self.temp.name) / "tampered"
        directory.mkdir()
        (directory / "model.joblib").write_bytes((self.directory / "model.joblib").read_bytes())
        write_json(directory / "manifest.json", self.manifest | {"threshold": .01})
        with self.assertRaisesRegex(ValueError, "Manifest"):
            load(directory, self.manifest["artifact_sha256"])
