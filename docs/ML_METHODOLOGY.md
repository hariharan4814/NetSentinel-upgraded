# ML methodology

## Implemented lab extension — 2026-10-05

The independent `lab/` package now generates metadata, trains Isolation Forest
and Random Forest, evaluates against dummy/rule comparators, and computes real
SHAP contributions. Its contract is [AI_LAB_CONTRACT.md](AI_LAB_CONTRACT.md).
All results are **SIMULATION**, with no network transmission, capture driver,
Django or database dependency in the core. The historical host-v1/LIVE protocol
below is preserved separately; these experiments do not validate or replace it.

### Reproducible procedure

Five configurable families generate payload-free `PacketMetadata` using reserved
documentation addresses: routine, bulk transfer, fanout, SYN burst and UDP burst.
Noise deliberately mixes distributions without changing the injected scenario
role. Challenge runs also contain routine windows. Thus features overlap and
some family labels are not recoverable from the seven aggregate inputs; accuracy
is not scripted. Missing observations remain null and are excluded with counts.

Each run receives a seed derived from the experiment seed, family and run index.
Whole runs are assigned before generation: floor(60%) training, max(1,
floor(20%)) validation, remainder test, independently within each family. No
window-level shuffle splits. The unchanged sensor aggregator produces seven
ordered host-v1 values in ten-second virtual windows. Only those numeric values
enter estimators: run IDs, seeds and the truth sidecar are excluded.

Isolation Forest uses 100 trees, benign training only, at most 256 samples/tree,
one CPU worker and a fixed seed. It flags negative `score_samples` strictly above
the linear 99th percentile of benign validation scores. Random Forest uses 100
trees, depth at most 12, minimum leaf size 2, balanced class weights, one worker
and the same fixed seed. It predicts an injected behaviour family, not an attack
or malware probability. Hyperparameters and heuristic thresholds are fixed and
not chosen from held-out metrics. The dummy predicts the most frequent training
family. Heuristic priority is UDP fraction >=0.7, SYN fraction >=0.55, remote
peers >=18, then IP bytes/second >=9000, otherwise routine.

Benign training quantiles provide descriptive references. TreeSHAP uses at most
64 all-family training rows as its background and explains the predicted class's
probability output; the implementation checks base plus contributions against
the actual classifier output within 1e-5. It describes the fitted model, not
causation. Unavailable SHAP produces a visible limitation, never invented values.

Default-configuration browser QA on 2026-10-06 found an important compatibility
case: TreeExplainer's parsed model matched Random Forest predictions, but its
interventional contributions disagreed by up to 0.03018. Explicit float32 inputs
did not resolve this. NetSentinel retains the 1e-5 output check across **all**
classes and falls back to the library's
[ExactExplainer](https://shap.readthedocs.io/en/latest/generated/shap.ExactExplainer.html),
calling the actual classifier with the same training-only background. Seven
features bound this to at most 128 coalitions, 64 background rows and eight
displayed cases. Cancellation is checked between cases; the worker also has an
owned-process time limit. Each case records its actual method, and the result
discloses fallback. No contributions are rescaled or manufactured to make the
check pass. This fallback still explains independent feature interventions and
can evaluate combinations outside the observed traffic distribution.

Classification metrics use all complete test windows. Per-class undefined
precision/recall/F1 use zero, explicitly following the zero-division convention;
balanced accuracy averages supported-class recall. Anomaly precision, recall,
false-positive rate and alerts/hour are null when their denominator is zero;
average precision is null unless both challenge and benign windows exist.
False alerts/hour divides flagged benign windows by complete benign **virtual**
ten-second observation time. It is not measured real-world alert burden.

```powershell
.\.venv-lab\Scripts\python.exe -m lab demo --out artifacts/lab/my-experiment
.\.venv-lab\Scripts\python.exe -m lab inspect artifacts/lab/my-experiment
.\.venv-lab\Scripts\python.exe -m lab generate --out artifacts/lab/my-dataset
.\.venv-lab\Scripts\python.exe -m lab benchmark --out artifacts/lab/my-study --seeds 42 43 44 --bootstrap-repetitions 200
.\.venv-lab\Scripts\python.exe -m unittest discover -s tests/lab -p test_pipeline.py -v
```

Choose unused output directories. Artifacts include dataset, separate truth,
splits, model, result and SHA-256/environment manifest. A model loader requires a
digest obtained independently from a trusted local run, checks the environment
and refuses LIVE bundles. An adjacent manifest alone cannot make joblib/pickle
safe. The public website and browser API cannot upload or activate these models.

### Additional study and measured limitations

The optional CLI benchmark supports two to five independent seeds and 50–1000
bootstrap replicates. It resamples **whole test runs** with the fitted estimator
fixed and reports conditional 95% percentile macro-F1 intervals. It retains all
five class positions; a resample missing a family has zero F1 for that family.
This conservative convention can produce wide intervals with few runs. It does
not estimate training uncertainty; sample standard deviation across seeds is
reported separately. Seeds are not selected for favorable results.

The excluded-family study removes all training runs for one challenge family
(default fanout), including their routine windows, then evaluates the excluded
family's held-out challenge windows. It reports forced known-class predictions
and Isolation Forest flagged fraction. The classifier has no open-set rejection
class. Isolation Forest already trains only on benign data; this is a stress
test of its deviation scores, not unknown-attack detection validation. Generator
noise can still produce overlapping styles in other families; this limitation
is deliberate and is not evidence of genuinely unseen real-world attacks.

Measured on 2026-10-05 using defaults (10 runs/family, 30 windows/run, intensity 1,
noise .15, gap probability .02) and seeds 42/43/44, with no test-driven tuning:

| Measure | Measured SIMULATION result |
| --- | --- |
| Random Forest macro-F1 mean / sample SD | 0.8806 / 0.0104 |
| Fixed heuristic macro-F1 mean / sample SD | 0.7864 / 0.0245 |
| Most-frequent macro-F1 mean / sample SD | 0.1059 / 0.0020 |
| Complete test windows by seed | 293, 293, 291; missing 7, 7, 9 |
| Random Forest conditional bootstrap intervals | [0.5567, 0.9028], [0.5228, 0.8933], [0.6767, 0.9148] |
| Isolation Forest challenge recall by seed | 0.0551, 0.1852, 0.2901 |
| False alerts per benign virtual hour | 2.1687, 9.1139, 2.2500 |
| Excluded fanout fraction flagged | 0.0000, 0.4375, 0.5814 |
| Three-seed study wall time | 13.41 seconds, excluding interpreter/import startup |

The weak and variable anomaly recall is an important negative result. The
conservative threshold and overlapping/noisy benign distributions often do not
separate generated challenge windows. Do not hide it behind classifier accuracy
or call the system a reliable intrusion detector. All data comes from the same
generator; external-network generalization remains unknown. Saved evidence is
ignored `artifacts/lab/repeated-seed-study-v2/benchmark.json`; the CLI reproduces
the numerical results, while timing depends on the machine.

Fresh scientific suite: 28 tests cover feature parity, no network I/O, deterministic
seeds, whole-run splits, sidecar isolation, gap handling, bounds, cancellation,
calibration/reference scope, test-label independence, actual SHAP additivity,
trusted reload parity/tampering, hand-calculated metrics and grouped bootstrap.
The final test outcome is recorded in plan.md. Temporal drift, feature ablations,
external-data evaluation and any local LLM remain unfinished extensions; the
single browser experiment does not silently include this separate study.

Source inspection identified two issues for that stage: `ml/pipeline.py` uses
fixed 180/60/60 row slices without ensuring complete runs stay in one partition,
and `backend/detection/explain.py` has a static reference fallback. Do not copy
those into the new experiment as verified run independence or learned references.
Preserve historical results with their limitations; a corrected protocol needs
new model/data versions and fresh evaluation, not relabelling of earlier results.

Reduced scope, 2026-09-11: Sprint 4 delivers one Isolation Forest on genuine traffic-derived host features; Sprint 5 adds observed-feature explanations and labelled labs. The existing seven-field host-v1 contract and sensor/tests are unchanged. No model has been trained, loaded or evaluated by this cleanup.

## Scientific claim

Isolation Forest estimates how unusual an observation is relative to its training distribution. It does not identify attacks or estimate attack probability. The required model output is **Normal** or **Anomalous**, determined by a documented calibrated threshold. Incomplete/incompatible/no-model windows are **unscored**, not Normal. Keep descriptive interpretations separate:

- **Anomalous behaviour:** model threshold exceeded; reason and baseline version visible.
- **Potentially suspicious behaviour:** behavioural/context rules support investigation; retain uncertainty and alternative benign explanations.
- **Evidence-supported known classification:** an explicit rule, verified external evidence, or analyst validation supports the named behaviour. Confirming an observed pattern does not automatically confirm a successful attack. Synthetic ground truth remains synthetic.

Normal means the evaluated window did not exceed this model's threshold; it is not a safety verdict. Evidence wording is separate from the model label; incident lifecycle and enterprise severity/risk fields are OUT OF SCOPE. Labels such as “port-scan-like fan-out” must describe supporting metadata, not attribute intent.

## Windows and features

MVP models score one host/selected-interface observation profile in nonoverlapping 10-second event-time windows, finalized after 2 seconds of lateness. Per-remote-device features/models are OUT OF SCOPE; previous attribution experiments remain historical. Host-only and unattributable forwarded-interface aggregates are different observation profiles and cannot share an active model without evaluation. IP/MAC discovery alone does not authorize per-device scoring.

The seven-field host-v1 contract is now frozen in [LIVE_FEATURE_CONTRACT.md](LIVE_FEATURE_CONTRACT.md), with exact missingness, direction, time and reconstruction fixtures. Sustained live validation remains open; freezing definitions does not authorize model training. Ordered vector (seven numeric values):

| Feature | Definition and required retained input |
| --- | --- |
| packets_per_second | Observed attributable IP packet count / valid window duration in seconds |
| ip_bytes_per_second | Sum of observed IP lengths / duration; not payload or physical-wire bytes |
| outbound_byte_fraction | Outbound IP bytes / (inbound + outbound IP bytes); 0 for an observed idle window |
| unique_remote_peers | Count of distinct remote IP endpoints in attributable host flows; not a count of discovered LAN devices |
| tcp_syn_fraction | TCP packets with SYN set / observed TCP packets; includes SYN+ACK, 0 if no TCP packets |
| udp_fraction | Observed UDP IP packets / all attributable IP packets; 0 if idle |
| mean_ip_packet_bytes | IP byte sum / IP packet count; 0 if idle |

Retain directional packet/IP-byte counts, TCP/SYN and UDP counts, flow endpoint tuples, attribution/parse/drop flags and window duration. They are sufficient to reconstruct these features; byte/packet totals alone are not sufficient for SYN fraction. Use flow segments and per-window sufficient statistics, not serialized packets. The idle convention applies only while capture is known active and complete. Unsupported fields do not become zero: mark the window/profile incompatible. Finalized valid host windows may be idle; minimum non-idle baseline coverage is required to avoid training a constant model.

Defer new-peer history, inter-arrival variation, full-connection duration/short-flow fractions, connection failure and reset-based heuristics until bounded sufficient statistics/state and parity tests exist. Cutting a connection every 10 seconds does not create short connections. DNS-name/payload features are excluded. Capture/offload and direction definitions are shared with NETWORK_SENSOR_PLAN.md.

Feature specifications must fix units, ordering, direction semantics, missing values, clipping/log transforms, and minimum completeness. Fit imputation/transforms only on training data. Tree models do not require scaling by default; any added scaler must be justified and saved with the pipeline. Exclude raw IPs, MACs, scenario labels, analyst annotations, and mode/run IDs from predictive inputs.

## Dataset and live-feature compatibility gate

Public dataset training is not required for the MVP. A model trained on arbitrary public flow CSVs must never be attached to live host windows by renaming columns, padding zeros or assuming both use a five-tuple. For example, [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) distributes captures and CICFlowMeter-derived labelled flow features; that does not establish compatibility with NetSentinel's fixed host windows.

| Input | Permitted use |
| --- | --- |
| Reviewed live metadata + saved sufficient statistics | Train/calibrate the matching live host profile using the shared feature implementation |
| Synthetic packet metadata | SIMULATION integration/demonstration and separately reported experiments; separate model assignment |
| Public PCAP with usable headers and label provenance | Later compatible REPLAY: re-extract using the exact pipeline; define host selection, visibility, timing and window-label mapping; packet payloads never become model inputs |
| Public feature CSV missing raw timestamps/packets or using different durations/directions | Separate offline benchmark/schema. It cannot reconstruct the live packet pipeline or justify a live model |

Promotion requires a compatibility manifest comparing observation unit, visibility/NAT side, direction, byte layer, flow timeout/window length, protocol/flag semantics, transform order, missing values, capture quality, feature order and label construction. Shared fixtures must give equivalent features within a specified numerical tolerance. Then evaluate on independent live benign activity to assess domain shift/false-alert burden. Replay agreement alone is insufficient to assert real attack accuracy. Until all checks pass, transfer remains experimental and the artifact is ineligible for LIVE activation.

## Baseline and model lifecycle

Collect consented normal activity across idle, browsing, streaming, downloads, and different time periods. Keep a reviewed manifest; benign collection may contain unknown anomalies. Train one host observation-profile model initially. A new adapter/profile or insufficient baseline shows “learning / ML unavailable” while real counters/flows remain useful. Avoid claiming learning completion from an arbitrary number of highly correlated windows; record distinct sessions/days, non-idle samples and feature variability.

### Pilot / Prototype Baseline Specification (Sprint 4)

For the Sprint 4 pilot/prototype baseline, the following requirements apply:
- **Minimum dataset size:** at least 300 eligible LIVE windows.
- **Run diversity:** at least 3 independent capture runs.
- **Temporal diversity:** at least 2 distinct UTC calendar dates.
- **Chronological split:**
  - **180 training windows** (earliest chronological segment).
  - **60 calibration windows** (used solely for p99 threshold selection).
  - **60 held-out test windows** (evaluated once after model and threshold freeze).
  - Any extra windows beyond the initial 300 required for the pilot split remain unused at the end of the chronological sequence to preserve exact split sizes.
- **Features:** All seven frozen host-v1 features are preserved without modification.
- **Provenance:** Baseline training uses strictly LIVE traffic (no synthetic or demo data).
- **Production recommendation:** Longer multi-day collection (e.g., 5+ runs across multiple working days with varied traffic patterns) is strongly recommended for production deployment to capture broader seasonal and diurnal variations.

Fit preprocessing/model on training only, select threshold on calibration only, and evaluate test once after choices are frozen. If sessions are insufficient, disclose exploratory results rather than reporting a reliable generalization estimate.

Reset rolling feature/rule context at split boundaries or explicitly reserve a preceding warm-up segment whose samples are not scored. Do not let duplicates, future peer history, labels or a later threshold choice leak backward. Group repeated scenario templates/seeds appropriately and reserve unseen variants for evaluation. Demonstration fixtures are development/integration data, separate from the locked research set. These controls follow the principles in scikit-learn's [data-leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).

Use fixed random seeds and record estimator parameters, feature/schema/library versions, input manifest hashes, time cutoffs, training duration, artifact digest, and environment details. Start with a small documented hyperparameter search suitable for the laptop. Never load untrusted joblib/pickle artifacts. Record a local operator's review, trusted artifact digest, compatible profile and actual loaded version; keep the previous compatible artifact for manual rollback. No enterprise registry/approval workflow is required. Collection continues if inference fails.

Begin with bounded training exports and single-worker model fitting/inference; avoid loading all retained telemetry into Pandas or consuming all CPU cores by default. Schedule offline training outside the demonstration capture run unless concurrent resource use has been measured. Record wall time and peak memory along with model quality.

Training, artifact transfer and model selection are manual/local. The sensor verifies the trusted local artifact and records the actual loaded version at a window boundary. Backend result metadata must reflect that actual version; no remote desired-assignment API is required. On failure it retains the previous compatible version or reports unavailable. Every finding carries the actual version; delayed findings retain their original version, not the newest assignment. Keep reviewed feature data long enough to reproduce training under a documented research-data retention exception, or provide a deterministic recollection recipe and disclose any inability to reproduce exactly.

In scikit-learn, lower score_samples values indicate greater abnormality; decision_function applies the learned offset. Define the application score explicitly as negative score_samples so larger means more unusual, and store a separately calibrated application threshold. Do not confuse that threshold with decision_function's zero cutoff. Contamination controls threshold-related behaviour, not a measured fraction of attacks. See the official [IsolationForest API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

## Explainable Threat Analysis

Explain observed deviations from training/calibration reference quantiles and transparent rule evidence, using only retained metadata and complete compatible windows. Store the feature/statistic, observed value and unit, reference value/range, comparison method, version, interval, mode/session and benign alternatives. These are descriptive comparisons, not causal explanations or guaranteed feature attribution within Isolation Forest.

| Explanation | Observed evidence / limitation |
| --- | --- |
| High packet rate | host-v1 packets_per_second compared with the reviewed baseline distribution; legitimate downloads/bursts may explain it. |
| Sudden traffic spike | ip_bytes_per_second compared with baseline or a documented bounded sequence of prior complete windows in the same session; reset on gaps/splits, never compare against invented zeros. |
| Unusually high outbound traffic | Retained outbound IP bytes / ten seconds plus outbound_byte_fraction, compared with baseline. A high fraction at tiny volume alone does not establish high outbound traffic or exfiltration. |
| Many destination ports | Count distinct outgoing destination ports per remote endpoint from directional TCP/UDP flow tuples in a complete window. It is explanation evidence, not an added host-v1 model feature. |
| Unusual flow count | Count distinct observed flow keys per complete ten-second window and compare with a reference. Call it flow count; these segments do not prove established, failed or complete connection counts. |

Destination-port and flow-count evidence must be derived from retained flows with independently checked expectations in Sprint 5. Preserve the seven model inputs unchanged; any later model-feature expansion needs a new schema and separate approval/evaluation. Missing headers/direction, partial coverage or absent reference makes the relevant explanation unavailable.

Prefer wording such as "Observed packet rate above the reference range" or "Many outgoing destination ports; possible suspicious behaviour." Only mention a possible attack, malware, exfiltration or port scan when specific corroborating evidence supports that tentative wording; the model score or high outbound volume alone is insufficient. Do not claim compromise, intent or confirmed attack. No LLM, external intelligence API or automatic blocking.

Transparent rules specify evidence, compatible profile, threshold, bounded context and benign alternatives. Rule findings can exist with ML unavailable and must be shown separately from Normal / Anomalous. Numeric explanation thresholds are proposed until calibrated/documented.

## Deterministic demonstration contract

Use an isolated SIMULATION run with a fixed seed, event timestamps and versioned rule manifest. Emit benign normalized metadata with at most three outgoing destination ports to one peer per ten-second window, followed by two consecutive complete windows each containing outgoing TCP SYN metadata to 24 distinct destination ports on that synthetic peer. No packets are transmitted.

The fixed **provisional demonstration rule** qualifies at 20 distinct outgoing destination ports per peer per complete window. The benign control yields zero qualifying windows; the two fan-out windows yield exactly two window-level rule findings, each reporting 24 observed ports and the threshold of 20. The UI may group them into one scenario summary while retaining both windows. With ML disabled the anomaly score/label is unavailable, and the rule evidence still explains the unusual fan-out. This threshold is a demo fixture, not a validated attack boundary.

Use stable (mode, run/session, window, peer, rule version) result identities so ingestion retries cannot duplicate findings. Reset state between runs; run twice and verify identical counts/features/rule decisions (UUIDs and processing times may differ). All results are calculated from generated metadata through shared aggregation/rules and actual ingestion when integrated, never preinserted display data.

The former risk formula 0.25A + 0.40B + 0.20C + 0.15P, risk-55 incident fixture, severity bands, asset weighting, incident correlation and notification cooldown policy are **historical / OUT OF SCOPE**, superseded by computed explanation findings. No such production engine exists to remove. Historical rationale remains in ARCHITECTURE_REVIEW.md.

Simulation is a reliable explanation/integration demonstration, not a requirement for Isolation Forest to flag the fixture. Keep it outside locked scientific test data. REPLAY may later use bounded PCAP or controlled datasets with explicit profile, event time, provenance and parser/privacy limits. Incompatible feature CSVs cannot become genuine LIVE or reconstructed packet streams.

## Evaluation and drift

Evaluate one Isolation Forest and the correctness/coverage of its descriptive explanations. Rules have separate benign/controlled behaviour checks; a complex multi-model or weighted-hybrid comparison is OUT OF SCOPE. Define evaluation unit (host window or correlated event) and what “positive” means before calculating metrics. Map external labels to windows using a documented rule and exclude/report ambiguous windows; never treat scenario titles as attack ground truth. Use precision/recall/F1/confusion matrices only with appropriate labels, and PR-AUC only when a meaningful continuous ranking and both classes exist. Do not invent PR-AUC for a binary-only rule. No positive cases means recall is undefined, not zero or 100%. Report event-level duplicate-adjusted counts as well as window metrics.

Report alerts per observed hour and, where reviewed, false alerts per reviewed benign hour; do not call every unreviewed live alert false. Device-normalized metrics require proven attribution; host/profile metrics are MVP. Include ordinary benign bursts, unseen benign sessions, latency, loss and CPU/RAM. Estimate variability over independent sessions/scenario runs rather than treating adjacent windows as independent; disclose small-sample limits. Analyze sensitivity of the model threshold and any explanation-rule thresholds using development/calibration data only.

Unlabelled live data supports observation and analyst review, not attack-detection accuracy claims. Simulation/replay results must be separate from live evidence. Publish scenario seeds, expected input behaviour, dataset licenses/provenance, limitations, sample counts and variability across seeds/runs. Do not tune on the final demonstration/test set.

Monitor feature drift and changing alert rates. Retraining is reviewed and manual initially; never train automatically on all incoming traffic or analyst labels. Retain prior model for rollback. Baseline contamination, concept drift, sparse host baselines, partial capture, and synthetic-to-live differences remain research limitations.
