/** SIMULATION-only browser contract. Never imports the native capture or model runtime. */
export const LAB_FAMILIES = ["routine", "bulk_transfer", "fanout", "syn_burst", "udp_burst"] as const;
export type LabConfig = { seed: number; runs_per_family: number; windows_per_run: number; intensity: number; noise: number; gap_probability: number };
export const DEFAULT_LAB_CONFIG: LabConfig = { seed: 42, runs_per_family: 10, windows_per_run: 30, intensity: 1, noise: .15, gap_probability: .02 };
export const CONFIG_LIMITS: Record<keyof LabConfig, [number, number, boolean]> = { seed: [0, 2147483647, true], runs_per_family: [6, 30, true], windows_per_run: [12, 120, true], intensity: [.5, 2, false], noise: [0, 1, false], gap_probability: [0, .15, false] };
export function validLabConfig(value: unknown): value is LabConfig {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const fields = value as Record<string, unknown>;
  return Object.keys(fields).every(key => key in CONFIG_LIMITS) && Object.entries(CONFIG_LIMITS).every(([key, [min, max, integer]]) => {
    const number = fields[key];
    return typeof number === "number" && Number.isFinite(number) && number >= min && number <= max && (!integer || Number.isInteger(number));
  }) && Number(fields.runs_per_family) * Number(fields.windows_per_run) * LAB_FAMILIES.length <= 20_000;
}
export type LabWindow = { id: string; run_id: string; window_index: number; time_seconds: number; truth_family: string; challenge: boolean; features: Record<string, number> | null; predicted_family: string | null; class_probability: number | null; anomaly_score: number | null; anomalous: boolean | null };
export type LabClassification = { model: string; labels: string[]; confusion_matrix: number[][]; accuracy: number | null; balanced_accuracy: number | null; macro_f1: number | null; per_class: { label: string; precision: number | null; recall: number | null; f1: number | null; support: number }[] };
export type LabExplanation = { window_id: string; method: string; predicted_family: string; base_value: number | null; output_value: number | null; additivity_error: number | null; features: { feature: string; value: number; reference_p95: number; contribution: number | null }[] };
export type LabResult = {
  schema_version: "lab-result-v1"; mode: "SIMULATION"; generated_at: string; config: LabConfig;
  dataset: { sha256: string; total_windows: number; valid_windows: number; unscored_windows: number; event_count: number; feature_names: string[]; splits: Record<string, { run_ids: string[]; windows: number }> };
  models: { name: string; task: string; parameters: Record<string, unknown>; training_windows: number }[];
  references: Record<string, { median: number; p05: number; p95: number; p99: number }>;
  classification: LabClassification[];
  anomaly: { threshold: number | null; precision: number | null; recall: number | null; false_positive_rate: number | null; average_precision: number | null; false_alerts_per_hour: number | null; scored_windows: number; unscored_windows: number };
  timeline: LabWindow[]; explanations: LabExplanation[];
  performance: { generation_seconds: number; training_seconds: number; evaluation_seconds: number; total_seconds: number; inference_p50_ms: number | null; inference_p95_ms: number | null; peak_rss_bytes: number | null };
  limitations: string[]; displayed_windows: number; total_test_windows: number;
};
export type LabJob = { id: string; status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED"; stage: string; created_at: string; updated_at: string; config: LabConfig; cancel_requested: boolean; completed: number | null; total: number | null; error: string; result?: LabResult };
export const labNumber = (number: number | null | undefined, digits = 3) => typeof number === "number" && Number.isFinite(number) ? number.toLocaleString("en", { maximumFractionDigits: digits }) : "Unavailable";
export const labPercent = (number: number | null | undefined) => typeof number === "number" && Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : "Unavailable";
export const familyName = (family: string | null) => family ? family.replaceAll("_", " ") : "Unscored";
export function progressPercent(job: LabJob): number | null {
  return typeof job.total === "number" && job.total > 0 && typeof job.completed === "number" && job.completed >= 0 ? Math.min(100, job.completed / job.total * 100) : null;
}
