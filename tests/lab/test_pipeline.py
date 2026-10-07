"""Synthetic-only scientific, provenance and numerical contract checks."""
import copy
import hashlib
import json
import random
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from sensor.features import FEATURE_NAMES, host_features
from sensor.flows import WindowAggregator
from lab.artifacts import load_trusted_bundle, write_artifacts
from lab.benchmark import group_bootstrap, run_benchmark
from lab.contracts import (DEFAULTS, ExperimentCancelled, FAMILIES,
                           canonical_json, digest, validate_config)
from lab.explanations import explain_windows
from lab.metrics import anomaly_metrics, classification_metrics
from lab.models import fit_models, partition, predict_features, vectors
from lab.pipeline import evaluate_dataset, run_experiment
from lab.simulation import (EPOCH, INTERFACE, LOCAL_IP, aggregate_packets,
                            generate_dataset, packet_window, split_runs)

CONFIG = {**DEFAULTS, "runs_per_family": 6, "windows_per_run": 12}


class ContractTests(unittest.TestCase):
    def test_invalid_config_and_large_integer(self):
        for value in (None, [], {"seed": True}, {"seed": 1.5}, {"seed": 10**1000},
                      {"noise": float("nan")}, {"noise": float("inf")}, {"mode": "LIVE"},
                      {"seed": -1}, {"windows_per_run": 121}, {"arbitrary_path": "x"}):
            with self.subTest(value=repr(value)[:100]), self.assertRaises(ValueError):
                validate_config(value)

    def test_defaults_are_copied(self):
        normalized = validate_config({})
        normalized["seed"] = 19
        self.assertEqual(DEFAULTS["seed"], 42)

    def test_no_identifiers_labels_or_nonfinite_inputs(self):
        good = dict(zip(FEATURE_NAMES, (1, 100, 0.5, 2, 0.1, 0.2, 100)))
        for features in ({**good, "family": "routine"}, {**good, "packets_per_second": True},
                         {**good, "udp_fraction": 1.1}, {**good, "mean_ip_packet_bytes": float("nan")},
                         {**good, "unique_remote_peers": 10**1000}, {"features": good}, None):
            with self.subTest(features=repr(features)[:100]), self.assertRaises(ValueError):
                vectors([features])
        np.testing.assert_array_equal(vectors([good]), [[1, 100, .5, 2, .1, .2, 100]])

    def test_missing_and_idle_are_distinct(self):
        self.assertIsNone(aggregate_packets([], start=EPOCH, run_id="test", missing=True))
        observed_idle = aggregate_packets([], start=EPOCH, run_id="test")
        self.assertTrue(all(value == 0 for value in observed_idle.values()))


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = generate_dataset(CONFIG)

    def test_deterministic_and_network_free(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
                patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
            second = generate_dataset(CONFIG)
        self.assertEqual(self.dataset, second)
        self.assertNotEqual(self.dataset["sha256"], generate_dataset({**CONFIG, "seed": 43})["sha256"])

    def test_existing_sensor_feature_parity(self):
        packets, _ = packet_window(random.Random(123), "fanout", EPOCH, CONFIG)
        aggregator = WindowAggregator(start=EPOCH, mode="SIMULATION", session_id="parity", interface=INTERFACE)
        for packet in packets:
            aggregator.advance(packet.timestamp)
            self.assertTrue(aggregator.add(packet))
            self.assertTrue(packet.source_ip.startswith(("192.0.2.", "198.51.100.")))
            self.assertFalse(hasattr(packet, "payload"))
        expected = host_features(aggregator.advance(EPOCH + 12)[0], {LOCAL_IP})
        self.assertEqual(aggregate_packets(packets, start=EPOCH, run_id="parity"), expected)
        self.assertEqual(tuple(expected), FEATURE_NAMES)

    def test_assignments_are_whole_run_disjoint(self):
        sets = [set(self.dataset["splits"][name]["run_ids"]) for name in ("train", "validation", "test")]
        for index, left in enumerate(sets):
            for right in sets[index + 1:]:
                self.assertFalse(left & right)
        self.assertEqual(len(set.union(*sets)), len(self.dataset["runs"]))
        self.assertEqual(len({row["seed"] for row in self.dataset["runs"]}), len(self.dataset["runs"]))
        for family in FAMILIES:
            for split in ("train", "validation", "test"):
                self.assertTrue(any(row["family"] == family and row["split"] == split for row in self.dataset["runs"]))
        for split, metadata in self.dataset["splits"].items():
            self.assertEqual(metadata["windows"], len(metadata["run_ids"]) * CONFIG["windows_per_run"])

    def test_labels_are_sidecar_and_not_predictive_inputs(self):
        for sample in self.dataset["samples"]:
            self.assertNotIn("family", sample)
            self.assertNotIn("challenge", sample)
            if sample["features"] is not None:
                self.assertEqual(set(sample["features"]), set(FEATURE_NAMES))
            self.assertEqual(set(self.dataset["truth"][sample["id"]]), {"family", "challenge"})

    def test_gap_changes_do_not_perturb_visible_traffic(self):
        complete = generate_dataset({**CONFIG, "gap_probability": 0})
        self.assertEqual(self.dataset["event_count"], complete["event_count"])
        gaps = 0
        for partial, full in zip(self.dataset["samples"], complete["samples"]):
            if partial["features"] is None:
                gaps += 1
            else:
                self.assertEqual(partial["features"], full["features"])
        self.assertGreater(gaps, 0)

    def test_cancellation_and_event_budget(self):
        with self.assertRaises(ExperimentCancelled):
            generate_dataset(CONFIG, cancelled=lambda: True)
        with patch("lab.simulation.MAX_EVENTS", 1), self.assertRaisesRegex(ValueError, "budget"):
            generate_dataset(CONFIG)

    def test_capped_window_and_valid_splits_at_all_limits(self):
        high = {**CONFIG, "intensity": 2.0}
        for family in FAMILIES:
            packets, _ = packet_window(random.Random(22), family, EPOCH, high, run_scale=100)
            self.assertLessEqual(len(packets), 512)
        for count in range(6, 31):
            runs = split_runs({**CONFIG, "runs_per_family": count})
            self.assertEqual(len(runs), 5 * count)
            self.assertEqual({row["split"] for row in runs}, {"train", "validation", "test"})


class MetricsTests(unittest.TestCase):
    def test_confusion_metrics_hand_calculated(self):
        actual, predicted = ["a", "a", "b", "b"], ["a", "b", "b", "b"]
        metrics = classification_metrics("test", actual, predicted, ["a", "b"])
        self.assertEqual(metrics["confusion_matrix"], [[1, 1], [0, 2]])
        self.assertEqual(metrics["accuracy"], .75)
        self.assertEqual(metrics["balanced_accuracy"], .75)
        self.assertAlmostEqual(metrics["macro_f1"], ((2 / 3) + .8) / 2)

    def test_anomaly_metrics_virtual_time_denominator(self):
        metrics = anomaly_metrics([False, False, True, True], [.2, .8, .9, .3], .5, unscored_windows=7)
        self.assertEqual(metrics["precision"], .5)
        self.assertEqual(metrics["recall"], .5)
        self.assertEqual(metrics["false_positive_rate"], .5)
        self.assertEqual(metrics["false_alerts_per_hour"], 180)
        self.assertEqual(metrics["scored_windows"], 4)
        self.assertEqual(metrics["unscored_windows"], 7)

    def test_zero_denominators_and_threshold_tie(self):
        metrics = anomaly_metrics([False], [.5], .5)
        self.assertIsNone(metrics["precision"])
        self.assertIsNone(metrics["recall"])
        self.assertIsNone(metrics["average_precision"])
        self.assertEqual(metrics["false_positive_rate"], 0)
        no_benign = anomaly_metrics([True], [.9], .5)
        self.assertIsNone(no_benign["false_positive_rate"])
        self.assertIsNone(no_benign["false_alerts_per_hour"])
        self.assertIsNone(no_benign["average_precision"])


class FittingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_dataset(CONFIG)
        cls.bundle = fit_models(cls.data)

    def test_threshold_and_references_have_correct_scope(self):
        benign = [row for row in partition(self.data, "train") if self.data["truth"][row["id"]]["family"] in {"routine", "bulk_transfer"}]
        x = vectors([row["features"] for row in benign])
        self.assertEqual(self.bundle["benign_training_windows"], len(benign))
        for index, name in enumerate(FEATURE_NAMES):
            self.assertAlmostEqual(self.bundle["references"][name]["p95"], np.quantile(x[:, index], .95))
        calibration = [row for row in partition(self.data, "validation") if self.data["truth"][row["id"]]["family"] in {"routine", "bulk_transfer"}]
        scores = -self.bundle["isolation_forest"].score_samples(vectors([row["features"] for row in calibration]))
        self.assertEqual(self.bundle["threshold"], float(np.quantile(scores, .99)))

    def test_test_labels_never_change_fitting_or_predictions(self):
        changed = copy.deepcopy(self.data)
        test = partition(changed, "test")
        for row in test:
            changed["truth"][row["id"]] = {"family": "routine", "challenge": False}
        second = fit_models(changed)
        x = [row["features"] for row in test]
        first_predictions, second_predictions = predict_features(self.bundle, x), predict_features(second, x)
        self.assertEqual(self.bundle["threshold"], second["threshold"])
        self.assertEqual(self.bundle["references"], second["references"])
        for key in first_predictions:
            np.testing.assert_array_equal(first_predictions[key], second_predictions[key])

    def test_shap_is_actual_additive_attribution(self):
        windows = partition(self.data, "test")[:3]
        explanations, warnings = explain_windows(self.bundle, windows)
        self.assertEqual(warnings, [])
        self.assertEqual(len(explanations), 3)
        for row in explanations:
            self.assertLess(row["additivity_error"], 1e-5)
            self.assertAlmostEqual(row["base_value"] + sum(item["contribution"] for item in row["features"]), row["output_value"], places=5)
            self.assertEqual(len(row["features"]), 7)

    def test_model_save_reload_parity_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = write_artifacts(directory, self.data, self.bundle, {"mode": "SIMULATION"})
            expected = manifest["files"]["model.joblib"]
            loaded = load_trusted_bundle(directory, expected_sha256=expected)
            features = [row["features"] for row in partition(self.data, "test")]
            original, restored = predict_features(self.bundle, features), predict_features(loaded, features)
            for key in original:
                np.testing.assert_array_equal(original[key], restored[key])
            self.assertNotIn("truth", json.loads((Path(directory) / "dataset.json").read_text()))
            with self.assertRaises(ValueError):
                load_trusted_bundle(directory, expected_sha256="0" * 64)
            with self.assertRaises(ValueError):
                load_trusted_bundle(directory, expected_sha256=None)
            blob = Path(directory) / "model.joblib"
            blob.write_bytes(blob.read_bytes() + b"tampered")
            with self.assertRaises(ValueError):
                load_trusted_bundle(directory, expected_sha256=expected)

    def test_live_bundle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SIMULATION"):
            predict_features({**self.bundle, "mode": "LIVE"}, [partition(self.data, "test")[0]["features"]])

    def test_evaluation_missing_windows_stay_unscored(self):
        evaluation = evaluate_dataset(self.data, self.bundle)
        missing = [row for row in evaluation["timeline"] if row["features"] is None]
        self.assertGreater(len(missing), 0)
        for row in missing:
            for field in ("predicted_family", "class_probability", "anomaly_score", "anomalous"):
                self.assertIsNone(row[field])
        self.assertEqual(evaluation["anomaly"]["unscored_windows"], len(missing))

    def test_training_cancellation(self):
        with self.assertRaises(ExperimentCancelled):
            fit_models(self.data, cancelled=lambda: True)

    def test_excluded_family_removes_whole_training_runs(self):
        bundle = fit_models(self.data, excluded_family="fanout")
        excluded = {run["id"] for run in self.data["runs"] if run["family"] == "fanout"}
        self.assertFalse(set(bundle["training_run_ids"]) & excluded)
        self.assertNotIn("fanout", bundle["random_forest"].classes_)
        with self.assertRaises(ValueError):
            fit_models(self.data, excluded_family="routine")


class EndToEndTests(unittest.TestCase):
    def test_default_experiment_has_additive_real_explanations(self):
        result = run_experiment(DEFAULTS)
        self.assertEqual(len(result["explanations"]), 8)
        for row in result["explanations"]:
            self.assertIn("SHAP", row["method"])
            self.assertLess(row["additivity_error"], 1e-5)
            self.assertAlmostEqual(row["base_value"] + sum(item["contribution"] for item in row["features"]),
                                   row["output_value"], places=5)

    def test_real_pipeline_artifacts_progress_bounds(self):
        progress = []
        with tempfile.TemporaryDirectory() as directory:
            result = run_experiment(CONFIG, output_dir=directory,
                                    progress=lambda stage, completed=None, total=None: progress.append((stage, completed, total)))
            self.assertEqual(result["mode"], "SIMULATION")
            self.assertEqual(result["schema_version"], "lab-result-v1")
            self.assertEqual(result["dataset"]["total_windows"], 360)
            self.assertEqual(len(result["classification"]), 3)
            self.assertLess(len(canonical_json(result)), 4 * 1024 * 1024)
            self.assertGreater(result["performance"]["peak_rss_bytes"], 0)
            self.assertGreater(result["performance"]["inference_p95_ms"], 0)
            self.assertEqual(progress[-1], ("complete", 1, 1))
            self.assertIn(("fitting_random_forest", None, None), progress)
            saved = json.loads((Path(directory) / "result.json").read_text())
            self.assertEqual(saved, result)
            manifest = json.loads((Path(directory) / "manifest.json").read_text())
            for name, checksum in manifest["files"].items():
                self.assertEqual(hashlib.sha256((Path(directory) / name).read_bytes()).hexdigest(), checksum)

    def test_cancellation_saves_no_success_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ExperimentCancelled):
                run_experiment(CONFIG, output_dir=directory, cancelled=lambda: True)
            self.assertFalse((Path(directory) / "result.json").exists())


class BenchmarkTests(unittest.TestCase):
    def test_bootstrap_resamples_whole_runs_not_individual_windows(self):
        # One wholly correct and one wholly wrong run: every resample has
        # either 0, 1 or 2 correct runs; no within-run fractional correctness.
        with patch("lab.benchmark.classification_metrics", wraps=classification_metrics) as metrics:
            report = group_bootstrap(["routine"] * 8, ["routine"] * 4 + ["fanout"] * 4,
                                     ["one"] * 4 + ["two"] * 4, seed=1, repetitions=50)
        for call in metrics.call_args_list:
            self.assertIn(call.args[2].count("routine"), (0, 4, 8))
        self.assertEqual(report["repetitions"], 50)
        self.assertIsNone(group_bootstrap(["routine"], ["routine"], ["one"], seed=1)["lower"])

    def test_benchmark_rejects_unbounded_or_ambiguous_inputs_before_work(self):
        for kwargs in ({"seeds": [1, 1]}, {"seeds": [1]}, {"seeds": [True, 2]},
                       {"seeds": [1, 10**1000]}, {"excluded_family": "routine"},
                       {"repetitions": 1001}, {"repetitions": True}):
            with self.subTest(kwargs=str(kwargs)[:100]), patch("lab.benchmark.generate_dataset") as generate:
                with self.assertRaises(ValueError):
                    run_benchmark(CONFIG, **kwargs)
                generate.assert_not_called()

    def test_repeated_seed_and_unknown_family_are_computed(self):
        report = run_benchmark(CONFIG, seeds=[42, 43], repetitions=50)
        self.assertEqual(report["mode"], "SIMULATION")
        self.assertEqual(len(report["runs"]), 2)
        self.assertNotEqual(report["runs"][0]["dataset_sha256"], report["runs"][1]["dataset_sha256"])
        for run in report["runs"]:
            unknown = run["unknown_family"]
            self.assertNotIn("fanout", unknown["trained_classes"])
            self.assertNotIn("fanout", unknown["forced_known_predictions"])
            self.assertEqual(sum(unknown["forced_known_predictions"].values()), unknown["scored_windows"])
            self.assertGreater(unknown["scored_windows"], 0)
            self.assertTrue(0 <= unknown["isolation_forest_flagged_fraction"] <= 1)
        self.assertAlmostEqual(report["summary"][0]["macro_f1_mean"],
            sum(run["classification"][0]["macro_f1"] for run in report["runs"]) / 2)


if __name__ == "__main__":
    unittest.main()
