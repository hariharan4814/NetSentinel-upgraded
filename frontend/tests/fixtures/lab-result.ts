import { DEFAULT_LAB_CONFIG, type LabResult } from "../../src/lib/lab-contract";

/** Labelled synthetic UI fixture, not training or scientific verification. */
export function labFixture(): LabResult {
  return {
    schema_version: "lab-result-v1", mode: "SIMULATION", generated_at: "2026-10-05T00:00:00Z", config: { ...DEFAULT_LAB_CONFIG },
    dataset: { sha256: "a".repeat(64), total_windows: 3, valid_windows: 2, unscored_windows: 1, event_count: 20, feature_names: ["packet_rate"], splits: { train: { run_ids: ["fixture-train"], windows: 1 }, validation: { run_ids: ["fixture-val"], windows: 1 }, test: { run_ids: ["fixture-test"], windows: 3 } } },
    models: [{ name: "Fixture classifier", task: "UI fixture only", parameters: {}, training_windows: 1 }], references: { packet_rate: { median: 1, p05: 0, p95: 2, p99: 3 } },
    classification: [{ model: "Fixture classifier", labels: ["routine", "fanout"], confusion_matrix: [[1, 0], [1, 0]], accuracy: .5, balanced_accuracy: .5, macro_f1: 1 / 3, per_class: [{ label: "routine", precision: .5, recall: 1, f1: 2 / 3, support: 1 }, { label: "fanout", precision: 0, recall: 0, f1: 0, support: 1 }] }],
    anomaly: { threshold: .6, precision: 0, recall: 0, false_positive_rate: 1, average_precision: .5, false_alerts_per_hour: 360, scored_windows: 2, unscored_windows: 1 },
    timeline: [
      { id: "fixture-1", run_id: "fixture-test", window_index: 0, time_seconds: 0, truth_family: "routine", challenge: false, features: { packet_rate: 2 }, predicted_family: "routine", class_probability: .7, anomaly_score: .7, anomalous: true },
      { id: "fixture-2", run_id: "fixture-test", window_index: 1, time_seconds: 10, truth_family: "fanout", challenge: true, features: { packet_rate: 1 }, predicted_family: "routine", class_probability: .8, anomaly_score: .4, anomalous: false },
      { id: "fixture-3", run_id: "fixture-test", window_index: 2, time_seconds: 20, truth_family: "routine", challenge: false, features: null, predicted_family: null, class_probability: null, anomaly_score: null, anomalous: null },
    ],
    explanations: [{ window_id: "fixture-1", method: "Synthetic test explanation - not computed training evidence", predicted_family: "routine", base_value: .5, output_value: .7, additivity_error: 0, features: [{ feature: "packet_rate", value: 2, reference_p95: 2, contribution: .2 }] }],
    performance: { generation_seconds: .1, training_seconds: .2, evaluation_seconds: .1, total_seconds: .4, inference_p50_ms: 1, inference_p95_ms: 2, peak_rss_bytes: 1000000 },
    limitations: ["SIMULATION UI test fixture. Invented fixture metrics must never be cited as model performance."], displayed_windows: 3, total_test_windows: 3,
  };
}
