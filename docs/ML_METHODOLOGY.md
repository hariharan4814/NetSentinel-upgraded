# ML methodology

## Scientific claim

Isolation Forest estimates how unusual an observation is relative to its training distribution. It does not identify attacks or estimate attack probability. Maintain three separate interpretations:

- **Anomalous behaviour:** model threshold exceeded; reason and baseline version visible.
- **Potentially suspicious behaviour:** behavioural/context rules support investigation; retain uncertainty and alternative benign explanations.
- **Evidence-supported known classification:** an explicit rule, verified external evidence, or analyst validation supports the named behaviour. Confirming an observed pattern does not automatically confirm a successful attack. Synthetic ground truth remains synthetic.

Classification, anomaly flag, severity, and incident lifecycle are independent fields. Labels such as “port-scan-like fan-out” must describe supporting metadata, not attribute intent.

## Windows and features

MVP models score one host/selected-interface observation profile in nonoverlapping 10-second event-time windows, finalized after 2 seconds of lateness. Per-remote-device features/models are experimental. Host-only and unattributable forwarded-interface aggregates are different observation profiles and cannot share an active model without evaluation. IP/MAC discovery alone does not authorize per-device scoring.

Freeze a small host feature v1 after Sprint 1. Proposed ordered vector (seven numeric values):

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

Feature specifications must fix units, ordering, direction semantics, missing values, clipping/log transforms, and minimum completeness. Fit imputation/transforms only on training data. Tree models do not require scaling by default; any added scaler must be justified and saved with the pipeline. Exclude raw IPs, MACs, scenario labels, incident dispositions, and mode/run IDs from predictive inputs.

## Dataset and live-feature compatibility gate

Public dataset training is not required for the MVP. A model trained on arbitrary public flow CSVs must never be attached to live host windows by renaming columns, padding zeros or assuming both use a five-tuple. For example, [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) distributes captures and CICFlowMeter-derived labelled flow features; that does not establish compatibility with NetSentinel's fixed host windows.

| Input | Permitted use |
| --- | --- |
| Reviewed live metadata + saved sufficient statistics | Train/calibrate the matching live host profile using the shared feature implementation |
| Synthetic packet metadata | SIMULATION integration/demonstration and separately reported experiments; separate model assignment |
| Public PCAP with usable headers and label provenance | Advanced REPLAY: re-extract using the exact pipeline; define host selection, visibility, timing and window-label mapping; packet payloads never become model inputs |
| Public feature CSV missing raw timestamps/packets or using different durations/directions | Separate offline benchmark/schema. It cannot reconstruct the live packet pipeline or justify a live model |

Promotion requires a compatibility manifest comparing observation unit, visibility/NAT side, direction, byte layer, flow timeout/window length, protocol/flag semantics, transform order, missing values, capture quality, feature order and label construction. Shared fixtures must give equivalent features within a specified numerical tolerance. Then evaluate on independent live benign activity to assess domain shift/false-alert burden. Replay agreement alone is insufficient to assert real attack accuracy. Until all checks pass, transfer remains experimental and the artifact is ineligible for LIVE activation.

## Baseline and model lifecycle

Collect consented normal activity across idle, browsing, streaming, downloads, and different time periods. Keep a reviewed manifest; benign collection may contain unknown anomalies. Train one host observation-profile model initially. A new adapter/profile or insufficient baseline shows “learning / ML unavailable” while real counters/flows remain useful. Avoid claiming learning completion from an arbitrary number of highly correlated windows; record distinct sessions/days, non-idle samples and feature variability.

Split chronologically by whole sessions into training, calibration, and locked test sets (provisional 60/20/20). Keep related devices/scenario runs together where necessary to prevent leakage. Avoid random overlapping-window splits. Fit preprocessing/model on training only, select threshold on calibration only, and evaluate test once after choices are frozen. If sessions are insufficient, disclose exploratory results rather than reporting a reliable generalization estimate.

Reset rolling feature/rule context at split boundaries or explicitly reserve a preceding warm-up segment whose samples are not scored. Do not let duplicates, future peer history, labels or a later threshold choice leak backward. Group repeated scenario templates/seeds appropriately and reserve unseen variants for evaluation. Demonstration fixtures are development/integration data, separate from the locked research set. These controls follow the principles in scikit-learn's [data-leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).

Use fixed random seeds and record estimator parameters, feature/schema/library versions, input manifest hashes, time cutoffs, training duration, artifact digest, and environment details. Start with a small documented hyperparameter search suitable for the laptop. Never load untrusted joblib/pickle artifacts. Registration, approval, activation and rollback are separate audited steps; activation verifies feature compatibility. Collection continues if inference fails.

Begin with bounded training exports and single-worker model fitting/inference; avoid loading all retained telemetry into Pandas or consuming all CPU cores by default. Schedule offline training outside the demonstration capture run unless concurrent resource use has been measured. Record wall time and peak memory along with model quality.

MVP training and artifact transfer are manual/local. The backend records desired assignments; the sensor checks the trusted local artifact and acknowledges the actual loaded version at a window boundary. Only then is activation applied. On failure it retains the previous compatible version or reports unavailable. Every finding carries the actual version; delayed findings retain their original version, not the newest assignment. Keep reviewed feature data long enough to reproduce training under a documented research-data retention exception, or provide a deterministic recollection recipe and disclose any inability to reproduce exactly.

In scikit-learn, lower score_samples values indicate greater abnormality; decision_function applies the learned offset. Define the application score explicitly as negative score_samples so larger means more unusual, and store a separately calibrated application threshold. Do not confuse that threshold with decision_function's zero cutoff. Contamination controls threshold-related behaviour, not a measured fraction of attacks. See the official [IsolationForest API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

## Threat interpretation and risk

Begin with one versioned transparent rule for outgoing destination-port fan-out using observable host metadata. Add sustained-rate rules only after evaluation; historical new-peer/reset rules are advanced. Each rule specifies minimum evidence, lookback, threshold, cooldown, benign alternatives and compatible profiles. MVP rule evaluation is local to the reusable pipeline with bounded session state; Django owns incident correlation. Rule-only findings may exist without an ML anomaly. Missing evidence is unknown, never proof of safety or danger.

Proposed prioritization formula: risk = round(100 × (0.25A + 0.40B + 0.20C + 0.15P)), each component bounded to [0,1]. A is the calibration-set empirical percentile of the anomaly score only when it exceeds the calibrated threshold (otherwise 0); B is a rule-defined evidence contribution (binary 0/1 for MVP fan-out); C is administrator-configured asset concern (default 0); P is rule-defined persistence (1 after two consecutive complete qualifying windows, otherwise 0 for this rule). Missing components contribute 0 but carry unavailable/completeness flags; do not renormalize. This is an unvalidated prioritization heuristic, not probability, and weights/bands need sensitivity analysis. An ML anomaly alone contributes at most 25 points and cannot create an incident.

Provisional bands: 0–24 informational, 25–49 low, 50–74 medium, 75–100 high. Open an incident when risk is at least 50 with qualifying rule evidence. Any later direct-rule override needs an explicitly versioned, evaluated policy; none is enabled by default. Persisting evidence may merit an investigation despite an ordinary ML score. Subject priority uses the maximum recent unresolved incident risk, never a sum of duplicate findings. Unknown attribution yields host/interface priority, not a fabricated remote-device score. Every score stores policy/components. No automatic blocking.

Explain a finding using feature deviations from training reference quantiles and triggered rule evidence. These are descriptive comparisons, not causal explanations or guaranteed feature attribution for the forest.

## Deterministic demonstration contract

Use an isolated SIMULATION run with a fixed seed, event timestamps and policy manifest. Emit benign normalized metadata with at most three outgoing destination ports to one peer per 10-second window, followed by two consecutive complete windows each containing outgoing TCP SYN metadata to 24 distinct destination ports on the same synthetic peer. No packets are transmitted. The fixed provisional rule qualifies at 20 distinct ports per peer per complete window; P becomes 1 after the second qualifying window. For a demonstration with ML disabled and C=0, B=1 and P=1 produce risk 55 and one medium-priority “potentially suspicious fan-out” incident.

Correlation key is (mode, scope, run/session, subject, peer, rule version); suppress duplicate notifications for 60 seconds of event time. The benign control must produce no incident with this policy. Reset all state between runs; run twice to verify identical counts/features/rule decisions (IDs and processing timestamps may differ). Incident rows and scores are calculated through the actual ingestion/domain services, never seeded as display data. If the rule/policy changes, update and reverify the fixture. This is a deterministic rule/integration demonstration, not a claim that Isolation Forest or any attack classifier must fire.

## Evaluation and drift

Compare Isolation Forest alone, rules alone and the hybrid on identical frozen inputs. Define evaluation unit (host window or correlated event) and what “positive” means before calculating metrics. Map external labels to windows using a documented rule and exclude/report ambiguous windows; never treat scenario titles as attack ground truth. Use precision/recall/F1/confusion matrices only with appropriate labels, and PR-AUC only when a meaningful continuous ranking and both classes exist. Do not invent PR-AUC for a binary-only rule. No positive cases means recall is undefined, not zero or 100%. Report event-level duplicate-adjusted counts as well as window metrics.

Report alerts per observed hour and, where reviewed, false alerts per reviewed benign hour; do not call every unreviewed live alert false. Device-normalized metrics require proven attribution; host/profile metrics are MVP. Include ordinary benign bursts, unseen benign sessions, latency, loss and CPU/RAM. Estimate variability over independent sessions/scenario runs rather than treating adjacent windows as independent; disclose small-sample limits. Analyze sensitivity of thresholds and risk weights using development/calibration data only.

Unlabelled live data supports observation and analyst review, not attack-detection accuracy claims. Simulation/replay results must be separate from live evidence. Publish scenario seeds, expected input behaviour, dataset licenses/provenance, limitations, sample counts and variability across seeds/runs. Do not tune on the final demonstration/test set.

Monitor feature drift and changing alert rates. Retraining is reviewed and manual initially; never train automatically on all incoming traffic or analyst labels. Retain prior model for rollback. Baseline contamination, concept drift, sparse device histories, partial capture, and synthetic-to-live differences remain research limitations.
