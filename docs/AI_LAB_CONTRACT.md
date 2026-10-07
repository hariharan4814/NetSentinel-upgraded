# AI Lab implementation contract — 2026-10-05

Status: implementation baseline for A1; tests/results recorded in plan.md.
Applies only to SIMULATION. Original LIVE host-v1 APIs/models remain unchanged.

## Scope of the first complete slice

Independent deterministic metadata generation through `sensor.WindowAggregator`
and `sensor.features.host_features`, real Isolation Forest and Random Forest,
rule/dummy comparators, run-separated evaluation, learned-reference/SHAP
explanations, a cancellable durable job workflow, local UI and semantic reports.
Use the existing seven host-v1 features first; temporal feature additions,
external-data evaluation and local LLM are subsequent extensions, not fake controls.

`lab.contracts.validate_config(object)` returns normalized settings; rejects
unknown keys, booleans in numeric fields, non-finite values and oversized inputs.
Defaults/limits: seed 42 (integer 0..2147483647), runs_per_family 10 (6..30),
windows_per_run 30 (12..120), intensity 1.0 (0.5..2.0), noise 0.15 (0..1),
gap_probability 0.02 (0..0.15). Mode is fixed SIMULATION, never supplied by UI.
Max 20,000 windows, 2,000,000 generated events, 512 events/window, bounded flows;
refuse/terminate over-budget runs explicitly. No actual packet/network emission.

Families: `routine`, `bulk_transfer`, `fanout`, `syn_burst`, `udp_burst`.
Routine/bulk have benign scenario roles; the other three are injected challenge
patterns, not proof of hostile intent. Include overlapping distributions, quiet
windows, benign high-volume cases and missing observations. The predictor sees
only numeric feature vectors. Labels/seed/run IDs live in a separate truth sidecar.

Assign whole runs before window generation, approximately 60/20/20 (at least one
validation and test run per family). Run seeds/configurations cannot cross sets.
Training statistics/SHAP background use training only. IF fits benign train and
uses benign validation p99 calibration. RF trains all train families; test data
does not set thresholds. Save split/config/data/model hashes and versions.
Scores are deviation/class output, not attack probability. Unscored is not benign.

## Pipeline callable, CLI and artifacts

`lab.pipeline.run_experiment(config, *, output_dir=None, progress=None,
cancelled=None) -> dict`.
`progress(stage, completed=None, total=None)` reports actual phases/counts;
`cancelled()` returns a bool, checked frequently. Raise
`lab.contracts.ExperimentCancelled` on cancellation, not a successful report.
No Django or database imports in the core. The worker supplies only a generated,
owned output directory. Native CLI may accept a user-selected output directory.

CLI: `python -m lab demo --out <directory>` with bounded config flags;
support dataset generation and reproducible evaluation/reloading where feasible.
Artifacts: JSON dataset/sidecar/split manifests, model bundle plus trusted manifest,
result JSON. No payloads, raw private inventories or untrusted pickle imports.
Use canonical JSON/hash, atomic writes and saved-model prediction parity tests.
Never register a lab bundle in the original LIVE model registry.

## Result JSON contract `lab-result-v1`

All keys below are real computed data; null means unavailable. No NaN/Infinity.
Full result JSON <=4 MiB; large window history is bounded for presentation and
explicitly reports total versus displayed. Provenance is always SIMULATION.

- `schema_version`, `mode`, `generated_at` UTC ISO, normalized `config`.
- `dataset`: `sha256`, `total_windows`, `valid_windows`, `unscored_windows`,
  `event_count`, `feature_names` (ordered strings), `splits` object with
  `train`/`validation`/`test`, each `{run_ids: string[], windows: number}`.
- `models`: array `{name, task, parameters, training_windows}` describing actual
  estimators/rules. `references`: per-feature `{median,p05,p95,p99}` from training.
- `classification`: array `{model, labels: string[], confusion_matrix: number[][],
  accuracy, balanced_accuracy, macro_f1, per_class: [{label,precision,recall,f1,support}]}`.
  RF, dummy and an explicitly heuristic rules comparator, same scored test set.
- `anomaly`: `{threshold, precision, recall, false_positive_rate, average_precision,
  false_alerts_per_hour, scored_windows, unscored_windows}`; zero denominators
  produce null. False-alert-hour denominator is benign virtual observation time.
- `timeline`: test-window array `{id,run_id,window_index,time_seconds,truth_family,
  challenge,features: object|null,predicted_family: string|null,
  class_probability: number|null,anomaly_score: number|null,anomalous: boolean|null}`.
  Feature object uses the ordered host-v1 keys; missing observations stay null.
- `explanations`: bounded selected cases `{window_id,method,predicted_family,
  base_value,output_value,additivity_error,features: [{feature,value,reference_p95,
  contribution}]}`. RF SHAP output semantics stated in `method`; TreeSHAP must
  pass an independent output check, otherwise bounded ExactExplainer evaluates
  the actual classifier over seven-feature coalitions. The method and fallback
  are disclosed; neither tolerance relaxation nor rescaling is allowed. Unsupported
  SHAP must surface an explicit unavailable message, not fabricated contributions.
- `performance`: `{generation_seconds,training_seconds,evaluation_seconds,
  total_seconds,inference_p50_ms,inference_p95_ms,peak_rss_bytes}` measured wall
  time/process memory; label sampling limitations.
- `limitations`: string[]; `displayed_windows`, `total_test_windows` integers.
Additional rigor experiments may add optional fields; clients handle their absence.

## Authenticated durable job API

Django `/api/v1/lab/` has fixed endpoints:

- GET `jobs/` -> `{jobs:[job]}` (newest 20).
- POST `jobs/` -> job, HTTP 201. Body `{config: settings}` only.
- GET `jobs/<uuid>/` -> job, optionally `result` on success.
- POST `jobs/<uuid>/cancel/` -> job, body `{}`.
- POST `worker/claim/` -> `{job: job|null, lease_token?: string}`, body `{}`.
- POST `worker/<uuid>/heartbeat/` -> `{cancel_requested: bool}`, body
  `{lease_token,stage,completed?: integer|null,total?: integer|null}`.
- POST `worker/<uuid>/finish/` -> job; body `{lease_token,status,result?,error?}`,
  status only `SUCCEEDED`, `FAILED` or `CANCELLED`; bound/redact failures.

Job: `{id,status,stage,created_at,updated_at,config,cancel_requested,completed,total,
error}` with UTC dates; detail can include result. Internal lease/token/artifact
paths never in browser job serializers. States `QUEUED,RUNNING,SUCCEEDED,FAILED,
CANCELLED`; interrupted expired jobs fail explicitly and require a new run.
Retain max20 jobs, queue4, running1; serialize admission/claim with database-backed
locking. Do not evict active work. No background thread training in Django.

Use new distinct `NETSENTINEL_LAB_TOKEN` (jobs) and
`NETSENTINEL_LAB_WORKER_TOKEN` (claim/heartbeat/finish). Existing read token can
read jobs; other scopes cannot mutate. Existing loopback/Host/Origin policy stays.
Worker result body max4 MiB only on authenticated finish; other requests stay64KiB.
Validate result structure/provenance and JSON size; reject unknown input keys.

`python -m lab.worker --base-url http://127.0.0.1:8001` runs in `.venv-lab`,
uses worker token from environment, fixed endpoint paths, no redirects/proxies,
heartbeat/lease, one job at a time and a 600s timeout. Use an owned child process
if needed so cancellation/timeout can stop estimator fitting; terminate only its
own child. Artifact root defaults to ignored `artifacts/lab/`; no HTTP path input.
Keep worker alive on empty queue until user stops it; document stop/recovery.

Backend owns a cohesive `experiments` app with migrations. One job model may
embed bounded config/result metadata rather than scaffolding four empty entities;
document the final schema. Shared lab validation may be a dependency-free import
with repository path made explicit; backend must never import ML packages.

ADR-035 adds an explicitly selected standalone `config.lab_settings` runtime:
own ignored SQLite database, experiments-only URLconf, production auth and
loopback checks, no research monitor routes or test credentials. Add a singleton
database lock row to serialize SQLite job writers before querying queue state;
retain the PostgreSQL advisory lock in original research settings. No automatic
fallback and no claim that this proves PostgreSQL migration/concurrency. The
original PostgreSQL runtime remains unchanged and currently unavailable locally.

## Next interface and public boundary

Authenticated local `/lab` reuses the operator login/session/CSRF interface.
Next `/api/lab/jobs` GET/POST, `/api/lab/jobs/<uuid>` GET,
`/api/lab/jobs/<uuid>/cancel` POST relay only these fixed job actions. Exact local
Origin, CSRF and session checks precede mutations. Tokens stay server-side; no
arbitrary destination URL. Bounded response <=4MiB, cancellation/timeouts and no
redirects. Read uses read token; mutation uses distinct lab token.

UI follows designplan: Scenario Studio form, actual job progress and cancellation,
saved experiment list, computed result charts/tables, replay/pause/step of recorded
test windows, separate truth overlay, model comparison, explanations, how-to and
PDF/JSON export. PDF is semantic jsPDF/AutoTable, not a dashboard screenshot.
All synthetic data is labelled; empty states contain no pretend example results.
No local LLM placeholder presented as functional AI. Preserve other routes/tools.
Keep `/lab`, gateway, jobs, models and resources outside public source allowlist.

## Required evidence

Tests: deterministic metadata/shared feature parity, no network I/O, sidecar
independence, disjoint run splits, gaps, bounds/cancellation, calibration scope,
model save/reload, hand-calculated metrics, actual SHAP additivity, auth/origins/
CSRF/scope/path/body limits, job retention/leases/restarts, browser full workflow,
PDF content/redaction/pagination and public export exclusion. Record any remaining
scientific suites (multi-seed confidence, unknown-family/drift, feature ablations)
as unfinished rather than inferring success from the initial demo.
