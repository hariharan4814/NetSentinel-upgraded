# NetSentinel AI Lab — execution plan and durable handoff

## Resume Here — 2026-10-07: core prototype verified

**Stop core implementation.** The requested local AI prototype is implemented and
verified on this Windows laptop. Do not repeat setup/downloads/migrations or start
optional extensions merely because historical checklist text remains below.
Current branch: `codex/ai-lab-prototype`. Starting commit: `65966ed`.
Implementation commits: `c233830` and final report correction `9a3d1ae`.
The documentation checkpoint follows those commits; use `git log -3 --oneline`
for its own commit ID. No merge into the default branch is authorized.

### Implemented and verified scope

- Independent seeded metadata simulator: routine/bulk-transfer benign roles and
  fanout/SYN/UDP challenge roles; shared host-v1 aggregation, missingness, bounded
  events and no packet transmission. CLI remains independent of Django/Npcap.
- Genuine Isolation Forest, Random Forest, dummy and rules baselines; whole-run
  train/validation/test separation, train-only references, held-out metrics,
  artifact hashes and trusted reload checks. No synthetic model promotion to LIVE.
- Real SHAP. Default TreeSHAP failed its independent additivity guard; exact SHAP
  over seven-feature coalitions now provides a bounded, disclosed fallback using
  the actual classifier and same training background. Tolerance remains 1e-5.
- Repeated-seed benchmark, whole-run bootstrap and excluded-family study. Weak
  anomaly recall is reported alongside classifier results; no desired score was
  manufactured. Drift/feature ablation and external validation are deferred.
- Authenticated loopback Next /lab, scoped Django job API, bounded queue/retention,
  separate spawned worker, cancellation, lease expiry and parent-death cleanup.
  Explicit standalone SQLite lab mode preserves original PostgreSQL research mode.
- Vanilla CSS glass UI: scenario settings, actual progress, saved experiments,
  recorded playback, truth overlay, explanation evidence, comparison, how-to,
  semantic PDF and JSON. Public export excludes all local routes and lab resources.
- Source launcher, setup/upgrade/recovery instructions, reproducible dependency
  lock, resource/license inventory and final-year demonstration guide.

### Verification ledger (actual commands, distinct scopes)

| Check | Result / date |
| --- | --- |
| `.venv-lab/Scripts/python.exe -m unittest discover -s tests/lab -p "test_*.py"` | 41 PASS, 26.107 s, Oct 7; 28 pipeline, 10 worker, 3 launcher |
| Backend `manage.py test tests --settings=config.test_settings` | 70 PASS, 2.504 s, Oct 6; includes temporary SQLite concurrency/restart |
| `manage.py makemigrations --check --dry-run --settings=config.test_settings` | No drift, Oct 6 |
| Explicit `config.lab_settings` system check | PASS with ephemeral credentials/temp DB, Oct 6 |
| Original sensor / ML / root publication suites | 93 / 18 / 3 PASS, Oct 5–6; no new live capture claim |
| Companion unit suite | 58 run, 53 passed and 5 environment-dependent skips, Oct 5 |
| Frontend `npm test` | 58 PASS, Oct 7 |
| Frontend lint / typecheck | PASS, Oct 6; final Oct 7 production build also typechecked |
| Production `npm run build` | PASS after final pagination correction, Oct 7 |
| Browser `npm run test:e2e` | 31 PASS, 1 existing opt-in LIVE skip, Oct 6; includes lab fixtures |
| `npm run build:public` and exclusion inspection | PASS, 34 files; only public routes, Oct 6; later changes affect excluded lab PDF only |
| `scripts/verify_ai_lab.py` real Next→Django→ML smoke | PASS Oct 7 after launcher/SHAP changes: authentication, CSRF/origin/input rejection, genuine 360-window training, cancellation, full-stack restart persistence |
| Actual browser default 1500-window experiment | PASS Oct 7: 8 valid exact-SHAP cases, saved result, desktop and 360px report downloads, no console errors |
| Semantic report | Final 10 pages rendered and individually inspected Oct 7; tables/section pagination corrected; real SIMULATION data, no private inventories |

The PDF renderer warned that Symbol/ArialUnicode display fonts were unavailable;
all report text uses the PDF's core Helvetica/ASCII path and rendered correctly.
The in-app download event waiter timed out, but the actual download completed;
the resulting file and mobile download were verified on disk. No product failure
was hidden. Initial integration harness sent partial settings and correctly got
HTTP 400; corrected to send the complete browser contract, without relaxing it.

### Preserved evidence and processes

- `artifacts/lab/integration-20261007-220124/verification.json`: final HTTP evidence.
- `artifacts/lab/browser-qa-20261006/experiments/856e32e1-6c30-4b6e-97d2-fc35e877cdac/`:
  genuine Oct 7 default result/models/manifests. 1500 windows, 178812 metadata
  events, 30 unscored observations; 12.71 s measured pipeline, 293.2 MiB sampled
  peak process RSS. This single measurement is not a hardware performance guarantee.
- `artifacts/lab/repeated-seed-study-v2/benchmark.json`: seeds 42/43/44, RF macro-F1
  mean 0.8806 (sample SD .0104), rules .7864 (.0245), dummy .1059 (.0020).
  IF challenge recall .0551/.1852/.2901; all generated-scenario results only.
- `output/pdf/NetSentinel-AI-Lab-SIMULATION.pdf`: final example, SHA256
  `618D6EA1543E4060CD57876187C722B939EDE254D921B39AF8532BF299BCE37A`.
- `artifacts/lab/desktop-verified.png`, `mobile-verified.png`; final PDF page images
  in `tmp/pdfs/release-*.png`. Generated outputs are ignored, not source dependencies.
- Old public outputs preserved at `artifacts/public-preserved-20261006-222512`
  and `public-release/dist.preserved-20261006-222512`; current export remains
  `public-release/dist`. No new remote site deployment was performed.
- All task-owned QA servers/workers are stopped; ports 8811/3105 checked clear.
  Original user `frontend/next-env.d.ts` remains uncommitted with exact SHA256
  `B8B3A344484B959AF5E4E3FC1A1609DAC3CB9ECE0CDEB6C145BE29BC4C491000`.

### Remaining limits and exact continuation

PostgreSQL verification is BLOCKED: original loopback connection timed out,
expected binaries/service were absent, and its existing data directory was not
modified. Restore the user's PostgreSQL installation, then run normal-settings
migration/check and concurrent job integration separately before claiming that
mode verified. SQLite acceptance does not stand in for PostgreSQL.

CICIDS2017 CSV is BLOCKED pending official access/registration information.
Local LLM assistant, public recorded AI showcase, temporal drift/ablation studies,
production Windows enforcement/signing and new live-hardware gates are DEFERRED.
These are not required for the delivered metadata-only simulation demonstration.
The existing public utility is preserved; there is no newly deployed public AI Lab.

To demonstrate now: follow `docs/AI_LAB_SETUP.md`; from repository root run
`.venv-lab/Scripts/python.exe scripts/run_ai_lab.py`, choose the local password,
and open its /lab URL. No admin, capture driver or paid API is needed. Ctrl+C
stops owned processes. Do not run Django test settings as a server.

Final release housekeeping: record the documentation commit, generate and inspect
the committed source ZIP per `docs/AI_LAB_RELEASE.md`, push this dedicated branch
if Git authentication permits, and create a draft PR only if an authorized GitHub
workflow is available. Git read access passed; `gh` and a PR creation connector
were not available at this checkpoint. Never merge main. If those external steps
remain unavailable, retain the local commits/artifact and report the limitation.

## Historical execution checkpoints (superseded by Resume Here)

## Active execution checkpoint — 2026-10-05

**Runtime refinement (ADR-035):** the original loopback PostgreSQL connection
times out; expected PostgreSQL binaries/service were not found, and its existing
data directory was not altered. To make the simulation prototype demonstrable,
add an explicit standalone lab runtime (`config.lab_settings`) using its own
ignored SQLite database and lab-only URL configuration. Original `config.settings`
and research persistence remain PostgreSQL. Serialize SQLite writers with a
database lock row; retain PostgreSQL advisory locks and its verification blocker.
Never report a SQLite demo as PostgreSQL acceptance. No existing dataset/token
or table is migrated into this mode. This is a separate supported lab startup,
not a test-settings bypass or silent fallback. Preserve all PostgreSQL tests.

**Resumed after usage interruption:** the branch and contract were saved; partial
`lab/contracts.py`, `lab/simulation.py` and Django `experiments`/auth changes are
present. No `.venv-lab` or `requirements-lab.lock` exists yet. The prior setup
command did not execute because automatic approval review hit an account usage
limit (not a safety finding). All old helper agents ended; inspect and finish
their partial work, re-run the normal scoped approval for setup, and do not claim
tests passed. Preserve original frontend edit. Current HEAD still `65966ed`.

User requested **Resume Work** after resource acquisition. Continue the approved
AI Lab implementation beginning with A1, retaining prior history below. A1 is
IN_PROGRESS. Save shared contracts before coding; then implement the independent
generator/training/evaluation pipeline, bounded Django job worker and authenticated
Next `/lab` interface. Additional agents may work on these disjoint modules as
authorized in the original task; only the primary agent maintains this plan.

Starting branch/commit were `codex/windows-companion-release` / `65966ed`.
Current implementation branch: `codex/ai-lab-prototype`, successfully created
without resetting the working tree. Shared interface saved in
`docs/AI_LAB_CONTRACT.md`. Assigned agents: ai_pipeline (independent lab/tests),
ai_jobs (Django/worker/tests) and ai_workbench (Next/CSS/reports/tests). Primary
agent owns integration, environment, verification and this shared progress log.
Preserve the uncommitted planning/resource changes and `frontend/next-env.d.ts`.
Continue on `codex/ai-lab-prototype`, without resetting or merging main.
Use a new ignored `.venv-lab` and the verified offline wheel lock; do not modify
the existing ML/sensor environments. Optional CICIDS2017 acquisition remains
BLOCKED and LLM weights/runtime DEFERRED. Initial vertical slice uses host-v1
features; additional temporal features require a separate tested contract.

Shared contract is saved and all 20 wheel hashes rechecked. `.venv-lab` was
created and the locked packages installed offline successfully; original
environments remain unchanged. `requirements-lab.lock` preserves their exact
versions/hashes. Current agents are lab_pipeline_finish, lab_jobs_finish and
lab_ui_finish after prior usage interruption. Next: finish CLI/jobs/UI, run
meaningful tests, then verify PostgreSQL/browser integration and rendered reports.
No end-to-end experiment success is claimed yet.

**Updated 2026-10-04 (Asia/Calcutta). Read this section first.** The user has
redirected the project toward a stronger M.Sc. Computer Science **AI research
prototype**, with generated normal and attack-like traffic, genuine model
training, simulation, explanations and evaluation. They explicitly requested a
clear plan before proceeding. The initial checkpoint was documentation only;
subsequent resource-only execution is recorded below. The lab is not yet
implemented or experimentally validated.

**Current execution instruction (2026-10-04): acquire external/online resources
first; application coding comes later.** Core R0 is VERIFIED for resource
integrity and offline dependency resolution only. Forty artifacts (about 129 MB)
are saved: 20 wheels, two official source distributions, three research PDFs,
licenses, publisher metadata and technical/model references. Inventory:
`resources/ai-lab/manifest.json`; guide: `resources/ai-lab/README.md`; candidate
acquisition lock: `resources/ai-lab/wheels-win-py311.lock`. Bulk files are ignored
by Git. Optional CICIDS2017 CSV is BLOCKED at official registration; no identity
was submitted or unofficial mirror substituted. Optional LLM weights/runtime
are DEFERRED; pinned official model documentation is cached. No package install,
downloaded-code execution, training, application coding or migration occurred.

The earlier release plan is preserved below as history. Its outstanding Windows
release gates remain valid for that product, but are not prerequisites for an
offline, metadata-only simulation lab. Do not resume the old release sequence in
preference to this plan. Use `YT.md` for the corresponding continuation notice.

## 1. Objective, problem and deliverable

**Working title: NetSentinel AI Lab — Explainable Network Anomaly Detection and
Traffic Simulation.** Suggested dissertation title: *Design and Evaluation of an
Explainable Network Anomaly Detection Prototype Using Reproducible Simulation*.

Students and junior analysts need a repeatable way to study unusual network
behaviour without administering an enterprise network, generating real attacks,
or treating an unexplained anomaly score as proof of compromise. The prototype
will let them create a virtual workload, train models, introduce unseen traffic
patterns, inspect predictions and explanations, and compare measured results.

The central workflow is **design a scenario → generate a dataset → train → test
unseen runs → explain → compare → export**. The traffic can be synthetic; model
fitting, inference, feature calculations and evaluation must actually execute.
No invented accuracy, hardcoded alert outcomes, simulated training spinner or
fabricated live data. A negative result or a false positive is useful evidence.

The original contribution is the reproducible experiment workflow, simulator,
provenance and leakage controls, explanation integration and comparative study;
do not claim to have invented Isolation Forest, Random Forest or SHAP.

### Scope and priority

- **Core:** offline metadata simulation, scenario controls, independent lab CLI,
  genuine Isolation Forest and Random Forest training, baseline comparisons,
  held-out evaluation, local authenticated workbench, explanations, reports and
  a reproducible viva demonstration.
- **Extension after the core works:** a local evidence-grounded AI assistant,
  one separately evaluated public-dataset benchmark, and a read-only public
  demonstration of a published synthetic experiment.
- **Preserve as supporting tools:** public connection helper, speed/IP/PDF
  tools, `/local`, independent sensor and Windows companion source. Present
  these separately from the main academic workflow. Do not delete working
  modules or require Npcap, administrator access, Defender or paid APIs for the lab.
- **Deferred:** new privileged Windows release work, real attack generators,
  autonomous response, custom antivirus, malicious-destination feeds, schedules,
  throttling, GAN/LSTM/autoencoder additions without a justified experiment,
  online self-training and automatic promotion of synthetic models to LIVE.

The product direction is requested by the user. The technical design and limits
below are the proposed implementation baseline, not completed capabilities.
Following the user's next instruction, resource acquisition was performed first;
application implementation remains future work, beginning with A1.

## 2. Repository assessment and actual environment

- Checkout: `C:\Users\yuvas\Desktop\NetSentinel`.
- Origin: `https://github.com/hariharan4814/NetSentinel-upgraded.git`.
- Current branch: `codex/windows-companion-release`.
- Starting/latest relevant commit for this plan:
  `65966edfd73f85370ed0ee65baa78a11b1a1d50d`.
- Recent work includes `9c76415` (implementation), `3712d39` (handoff/setup) and
  `65966ed` (documentation reconciliation). Preserve these commits and history.
- Pre-existing uncommitted change: `frontend/next-env.d.ts`. Preserve it. The
  file hash at assessment was
  `B8B3A344484B959AF5E4E3FC1A1609DAC3CB9ECE0CDEB6C145BE29BC4C491000`.
- Windows PowerShell; existing Python 3.11 environments `.venv`, `.venv-ml`,
  `.venv-backend`, Node 24.19.0 and `frontend/node_modules` were recorded in the
  prior checkpoint. A fresh `.venv` Python launch for a document check failed
  with “Unable to create process” for the referenced Python311 interpreter.
  Cause is not established; verify interpreter availability/execution permission
  before implementation. Native PowerShell completed the document checks instead.
  No dependency installation or hardware benchmark was performed for this plan.
- R0 follow-up: `.venv-ml` Python 3.11.0 and pip 22.3 run successfully with scoped
  execution permission outside the restricted sandbox. Downloading and offline
  resolution passed without environment reconstruction or installation. The
  earlier startup limitation is not evidence of a broken Python installation.
- Shell/file inspection and primary-source web research are available. Local
  browser, PostgreSQL, GPU/LLM runtime, hosting access and Git write permissions
  are not newly verified by this planning turn. CPU-first is a design constraint.
- User reports Npcap installation complete; prior checkpoint records successful
  preflight and eligible adapter. This is not verification of application-byte
  attribution or firewall blocking. No capture or privileged operation is needed
  for the planned simulation.

### Implemented foundation observed in source

| Area | Actual foundation | Gap relevant to this project |
| --- | --- | --- |
| Sensor | `sensor/models.py`, `flows.py`, `features.py`; bounded metadata, frozen seven-field host-v1 | No configurable student-facing scenario generator |
| ML | `ml/pipeline.py`, `ml/__main__.py`; real Isolation Forest training, calibration, manifests and scoring | No comparative experiment workbench or supervised lab model |
| Splits | Existing validation requires multiple runs/dates, then slices rows 0:180, 180:240, 240:300 | These boundaries do not enforce disjoint runs; an existing test name/documentation overstates the guarantee |
| Explanations | `backend/detection/explain.py` supports a supplied reference | Default `BASELINE_REFERENCE` is static, not learned from the current model's training data |
| Research UI | Next `/local`, local operator session, Django scoped tokens and PostgreSQL | UUID-centric monitor rather than scenario/training/evaluation workflow |
| Public/companion | Connection tools, approximate quotas, status/scans, reports and release scripts | Useful supporting products, not a coherent AI research demonstration |
| Tests | Separate sensor, ML, backend, companion and frontend suites | Root discovery alone finds publication tests; it is not the complete sensor or ML suite |

The old host model loader requires an exact IsolationForest and seven features.
Do not disguise a Random Forest or a larger feature vector as `iforest-host-v1`.
New lab bundles require their own versioned contract and registry.

Source/document drift to reconcile in A1: public lookup is `ipwho.is`, not the
`ipapi.co` named in some current docs; speed history and HTTP-check history have
different bounds; current auth variables are `NETSENTINEL_*`, not the alternate
names in some summaries; companion SQLite table names must be checked against
`companion/store.py`; older split/run-count and blanket verification statements
must be qualified. Keep dated historical evidence, but correct active contracts.

No application test totals from earlier handoffs are fresh results for this plan.

## 3. Modules and expected user experience

### M1 — Scenario Studio

Provide a guided starter scenario and an advanced editor with workload mix,
seed, virtual duration, anomaly onset, bounded intensity and background noise.
Show a virtual network map and timeline calculated from generated metadata.
Support start, pause, single-window step, restart, cancellation and playback
speed. Display virtual event time separately from elapsed computation time.

Core workload families: idle periods, web-like bursts, media-like UDP, software
downloads and background uploads; challenge patterns: destination/port fan-out,
SYN-heavy bursts, UDP-heavy bursts and unusually large outbound transfer.
Include legitimate high-volume activity and administrative discovery as hard
negatives. Periodic beacon-like behaviour is a later temporal-feature experiment,
not an assertion that seven host-v1 values can identify a beacon.

“Good traffic” and “bad traffic” may be introductory scenario labels, but explain
them as **configured benign workload** and **simulated attack-like challenge**.
Identical observable traffic can have different intent. Predict behaviour, not
malware identity, exfiltrated content or proof of a successful attack.

Generate in-memory `PacketMetadata` using documentation-only virtual addresses,
then reuse the existing flow aggregation and host feature calculations where
compatible. Do not emit packets, contact target machines or require capture.
Generate distributions with overlapping sizes/rates/timing, mixed workloads,
variable onset and explicit missing observations; avoid trivially separable
fixed values. All randomness must use recorded deterministic seeds.

Keep generated truth in an evaluation sidecar. Scenario names, labels, seed,
case IDs, IP-address categories and generator flags cannot be predictor inputs.
Use an independent random stream for label-free background generation so that
unrelated draws do not accidentally become class identifiers.

### M2 — Dataset and Feature Lab

Show sample counts, independent runs, scenario coverage, gaps, class balance,
feature distributions and split membership. Preserve the seven host-v1 formulas.
Start with host-v1 as a benchmark. Add a separately named `lab-features-v1` only
after defining and testing every formula and missingness rule.

Candidate additional features: distinct remote ports, outbound small-packet
fraction, interarrival variability, novelty relative to earlier destinations,
and a causal rolling volume ratio. These are proposals until reconstructibility
tests pass. Temporal state resets at run boundaries; warm-up and missing windows
are explicitly unscored. Fit statistics and novelty baselines without future data.

Initial dataset budget proposal: 100 independent 20-minute virtual runs,
10-second windows, approximately 12,000 windows before exclusions. The existing
20,000-row guard is not to be silently bypassed. Bound generated events, flows,
memory and wall time separately; virtual high rates must not create unbounded
millions of objects. If event budgets truncate observation, mark coverage invalid
rather than pretending downsampling preserves all seven features.

### M3 — Training Lab: actual machine learning

1. **Isolation Forest:** fit on reviewed/configured benign training runs, with
   threshold calibrated on separate benign validation runs. Score deviation from
   that baseline. Preserve original LIVE training independently.
2. **Random Forest classifier:** predict configured traffic-behaviour families
   such as routine, bulk transfer, fan-out, SYN-heavy and UDP-heavy activity.
   Train on labelled lab training runs. Do not call class probability the
   probability of malware or a calibrated confidence without calibration evidence.
3. **Comparators:** a fixed, documented rules baseline and DummyClassifier;
   optionally add a simple linear classifier when it answers a research question.
   Compare like tasks on identical split manifests, not unrelated score scales.

Display dataset/model versions, feature set, train/validation membership,
bounded hyperparameters, seed and model card. Training progress is based on
actual stages: validating, generating, fitting, evaluating, saving. RF/IF fitting
has no invented epochs or percentage; allow cancellation through the worker.

Keep anomaly score, behaviour prediction and deterministic rule evidence as
separate outputs. Do not introduce an arbitrary weighted “security score”. A
disagreement/abstention rule must be explicit and evaluated if added.

### M4 — Detection Console and explanations

Stream generated windows through the selected fitted model. Charts and counts
derive from computed outputs. Show anomalous, within-baseline and unscored
states; show injected truth in a separately labelled evaluation layer that can
be hidden before prediction. Include a useful quiet run with no alerts.

Use training-derived quantiles for anomaly explanations with their reference
version. Use SHAP TreeExplainer for the supported classifier configuration;
record output space and training-only background, verify additivity, and bound
sample/background counts. Show top contributing features, feature values,
reference range, alternative benign explanation and limitations. SHAP explains
the model's output, not causation or attacker intent.

Support a what-if comparison by changing a scenario parameter and actually
regenerating/rescoring the experiment. Do not fabricate a counterfactual safety
verdict or silently alter past results. A baseline shift/benign-drift scenario
can demonstrate false positives and explicit retraining with a new model version.

### M5 — Evaluation, comparison and research reports

Compare models and feature sets using the protocol in section 4. Include
confusion matrices, per-class precision/recall, macro F1, balanced accuracy,
ranking metrics for a clearly defined binary task, false-alert burden, coverage,
detection delay and measured resource usage. Expose class support and unavailable
metrics. A single accuracy percentage is not sufficient.

Create PDF and machine-readable JSON/CSV reports from saved results, reusing the
existing semantic reporting approach. Include generator/model/features/split
versions, seeds, data hashes, period, metrics, plots, limitations and SIMULATION
labels on every report. Tables paginate; charts have readable labels; long run
names wrap; sensitive host paths/addresses are excluded by default. Never export
private existing LIVE datasets as sample reports.

### M6 — Optional local AI experiment assistant

After the core is evaluated, integrate a small local instruction model to answer
questions such as “Why was this run flagged?” or “Why did these models disagree?”
Use redacted structured experiment facts and a small curated project-methodology
index; answers cite run/window/model or document identifiers. Numeric claims must
come from tool-free supplied facts and be validated against them. Treat scenario
names and imported text as untrusted input.

Candidate model: official `Qwen/Qwen3-4B-Instruct-2507`, Apache-2.0. Check runtime,
quantization provenance/license, RAM and latency before pinning a model revision.
Download only after explicit user-started setup; no API key or paid service is
required. It cannot run commands, capture traffic, modify models, block apps or
control Defender. On absent model/runtime, show unavailable or a clearly labelled
deterministic summary; do not pretend a template is an LLM response.

## 4. Scientific protocol and acceptance of claims

Research questions:

1. Do the models generalize to unseen generated runs and parameter combinations?
2. How do they compare with rules on the same anomaly task, including legitimate
   high-volume hard negatives and previously unseen challenge families?
3. Do added temporal/context features help, and at what cost to false alerts,
   coverage, latency and explainability?
4. Are explanations faithful to the saved model, reproducible and useful for
   tracing a result to its measured features?

Protocol:

- Assign entire independent runs to train/validation/test, initially 60/20/20 by
  group, stratified where feasible. Keep sibling configurations/near-duplicate
  trajectories in one group. Never split adjacent windows from the same run
  across sets. Publish group IDs and assertions in the split manifest.
- Tune on grouped folds within training or the declared validation set; fit
  transforms, quantiles and SHAP background only on training. Freeze thresholds
  and hyperparameters before final test. Record repeated test inspection; a
  revised experiment requires a new version and a fresh untouched final set.
- Use multiple predetermined seed collections and show variation. Confidence
  intervals should resample independent runs, not pretend correlated windows are
  independent. Report support and undefined metrics instead of zero-filling them.
- Separate behaviour-family classification from binary out-of-baseline detection.
  The evaluator's challenge label is synthetic ground truth, not evidence of
  malicious intent in actual network traffic. Include ambiguous/hard-negative
  cases and report errors honestly rather than tuning them out of the generator.
- Include deployment-like imbalanced challenges (proposed 1% and 5% challenge
  windows), an unseen-family holdout, benign workload drift and known gaps.
  Compare the same eligible windows; show excluded windows and coverage.
- Record precision/recall/F1 per class, macro F1, balanced accuracy, confusion
  counts, average precision/PR curves for a declared binary target, false alerts
  per benign **virtual hour**, and detection delay from virtual challenge onset.
  Measure inference p50/p95, fitting wall time and peak process RSS on the actual
  laptop. Virtual playback speed is not model throughput evidence.
- Test label-sidecar independence, duplicate rejection, group separation,
  time-causal features, saved/reloaded prediction parity and explanation
  reconstruction. Include a shuffled-label sanity control and host-v1/context
  feature ablation. No chosen minimum “99% accuracy” or predetermined winner.
- Conclusions from generated data are restricted to this simulator/distribution.
  Do not claim real-world intrusion detection accuracy or LIVE model compatibility.

Optional external benchmark: use the official CICIDS2017 labelled flow CSVs
with provenance/citation review, dataset-specific features and separate manifests.
Audit identifiers, duplication and time/session leakage; do not select a random
row split simply to improve metrics. Use a bounded documented subset and show
what was excluded. This is a separate benchmark, not a renamed host-v1 dataset
or mixed synthetic/real test. Raw PCAP/payload downloads are unnecessary. The
core demo must work offline without this dataset.

## 5. Architecture, persistence and security boundaries

```text
Local Next /lab (operator session, CSRF, loopback)
  -> fixed authenticated Django experiment API
  -> durable bounded jobs + one explicitly started worker
  -> independent lab Python pipeline
       metadata generator -> shared aggregates -> features -> trained models
       evaluation truth sidecar --------------------------> evaluator only
  -> local versioned artifacts + PostgreSQL metadata -> reports

Existing sensor -> existing /local/LIVE pipeline (preserved and isolated)
Public static site -> optional reviewed synthetic report/replay assets only
Windows companion -> existing independent local controls (no lab privileges)
```

- Proposed independent package `lab/`: contracts, scenarios, generator,
  features, datasets, splits, models, evaluation, explanations, artifacts and
  CLI. Shared pure contracts stay independent of Django models and network access.
  First deliver a tested CLI vertical slice before the web orchestration.
- Add one cohesive Django `experiments` app, not a platform rewrite. Proposed
  persisted entities: ExperimentRun/job, DatasetManifest, LabModelRun and
  EvaluationResult. Record immutable config/version/hash/provenance and artifact
  references; feature chunks stay in a bounded ignored local artifact directory.
  Finalize schema/API in `DATABASE_PLAN.md`, `API_PLAN.md` and migrations before
  use. Do not modify existing companion SQLite schemas for this work.
- A dedicated ML worker uses the ML environment; the Django web environment
  need not import scikit-learn. Prefer fixed loopback claim/heartbeat/result
  endpoints and distinct worker credentials so the worker stays framework-free.
  Claim ownership atomically, use leases and idempotent completion, and mark
  interrupted jobs explicitly. Do not train inside a request or introduce Redis/
  Celery merely for a single laptop. Keep core CLI usable without PostgreSQL.
- Proposed initial limits: one running job, four queued jobs, 20 retained runs,
  500 MiB artifact budget, 20,000 feature rows/dataset, bounded metadata events
  and 10-minute wall-time limit per default job. Final limits require resource
  measurement; refuse oversized requests before generation. Deletion affects only
  owned lab artifacts, never existing models/private captures. Pin/report a run
  before eviction; do not silently delete the user's selected dissertation result.
- API accepts schema-validated scenario presets and bounded numeric options,
  never code, scripts, executable paths, arbitrary file paths, pickle uploads,
  external target URLs or PowerShell. Resolve generated artifact IDs server-side,
  enforce root containment, permissions and trusted hashes before model loading.
- Extend operator authentication to `/lab`. Next mutations require exact local
  Origin/Host, server session and CSRF protection; Django enforces read/job/worker
  scopes independently. Separate new job credentials from sensor/model tokens;
  fail closed if absent. Do not trust forwarded headers without a trusted proxy.
- All lab data/model manifests use SIMULATION; playback retains source provenance.
  REPLAY and LIVE remain explicit independent modes. A synthetic model cannot
  be activated in the original LIVE registry. No anomaly-driven blocking.
- Keep `/lab`, jobs/APIs, Python, artifact directories, models and secrets out of
  the public static export. Any public demo contains only reviewed non-private
  synthetic result assets and clearly says “recorded simulation”. Static hosting
  cannot run the Python training job; training controls belong to the local app.
- No payloads, passwords, browsing URLs or packet files. Default generator sends
  no network traffic. Optional external dataset/model downloads require a distinct
  setup action and notice; ordinary simulation/training runs offline.

## 6. Open-source selection and dependency policy

Primary sources checked during the 2026-10-04 assessment. Selection is not an
installation or security-audit claim; perform compatibility/advisory review at
the implementation checkpoint and pin exact tested additions with lockfiles.

| Component | Purpose and decision | License / obligations |
| --- | --- | --- |
| Existing scikit-learn 1.9.0 | Reuse IsolationForest, RandomForestClassifier, DummyClassifier, metrics and group splitting; retain current compatible requirements initially | [BSD-3-Clause](https://github.com/scikit-learn/scikit-learn/blob/main/COPYING); preserve notice/disclaimer |
| SHAP | Version 0.51.0 source/wheel cached for Python 3.11; 0.52.0 requires Python 3.12. Runtime/additivity spike pending; no install | [MIT](https://github.com/shap/shap/blob/v0.51.0/LICENSE); retain notice; document background/output semantics |
| Qwen3-4B-Instruct-2507 | Optional local explanation assistant; exact weight revision/runtime and quantization not yet selected | [Official model card, Apache-2.0](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507); preserve applicable license/notices; recheck redistributed variants |
| CICIDS2017 | Optional separate external research benchmark, not required generator input | [Official dataset/citation terms](https://www.unb.ca/cic/datasets/ids-2017.html); do not describe dataset as MIT code; verify terms before redistribution |
| Existing Next/React/Django, jsPDF/AutoTable and ReportLab | Reuse UI, APIs and report generation rather than adopting an unrelated platform | Preserve current lockfiles and third-party notices; review any new report dependency separately |
| Existing Scapy/sensor | Reuse pure metadata contracts/aggregation; simulator does not require packet sending | Existing Scapy GPL obligations still apply where distributed; do not bundle Npcap or assume its redistribution rights |

References for implementation: [scikit-learn group-aware validation](https://scikit-learn.org/stable/modules/cross_validation.html),
[Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html),
[SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).

No root project LICENSE was found in the assessment's tracked/source file
listing. Choosing a license for original project code requires the author's
decision before describing the entire distribution as open source. Existing
dependency permissions do not grant a license to NetSentinel itself. This does
not block local prototype work. Do not clone unknown attack script collections
or install a large security platform merely to add feature names.

## 7. Ordered implementation tasks and acceptance gates

States: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `VERIFIED`, `BLOCKED`,
`DEFERRED`. Code existence permits IMPLEMENTED only; VERIFIED requires recorded
tests/evidence appropriate to the claim. Tasks A1–A8 are the core dissertation.

| ID | Task and relevant files | State | Acceptance criterion |
| --- | --- | --- | --- |
| A0 | Assessment, durable plan, design, ADR and handoff pointers | VERIFIED | Documentation saved; diff/links/fences checked; historical plan and pre-existing frontend edit preserved; no app verification implied |
| R0 | Official core external resource acquisition and inventory, requested before coding | VERIFIED | 40 artifacts checked, 20-wheel offline resolution passed, installed environment unchanged; R0-D/R0-M explicitly separate |
| R0-D | Optional external CICIDS2017 CSV acquisition | BLOCKED | Official registration needs user-provided details/link; no dataset downloaded or identity submitted |
| R0-M | Optional LLM weights and inference runtime | DEFERRED | Official card/config/license pinned and cached; select runtime/quantization/hardware fit before weights |
| A1 | Reconcile active contracts; define lab schemas, scenario taxonomy, feature formulas, group split and research protocol | VERIFIED | Source/doc discrepancies listed above resolved; versioned schemas and scope tests specified; implementation branch/checkpoint recorded |
| A2 | Independent metadata generator and CLI; `lab/`, `tests/lab/` | VERIFIED | Seeded reproducible scenarios, useful benign run and injected challenges; no network I/O; bounded data; gaps/virtual time/cancellation tested |
| A3 | Dataset manifests, run-group splits, real IF/RF/baselines and trusted lab bundles | VERIFIED | Disjoint groups, no label leakage, train-only references, saved/reloaded parity, genuine unseen-run predictions; old LIVE loader rejects lab bundle |
| A4 | Evaluation, explanations and reproducible experiment comparison | IMPLEMENTED | Metrics recompute from raw predictions; additivity/reference tests; imbalance/hard-negative/unknown-family cases; no fixed desired result |
| A5 | Django experiment metadata/migrations, bounded worker/API and auth | VERIFIED | Fresh DB migration and upgrade checks; unauthorized/origin/path requests rejected; lease/cancel/restart/retention tests; CLI still independent |
| A6 | Next `/lab` Scenario Studio, Training, Detection, Explain & Compare | VERIFIED | Complete user workflow uses computed data; real stage states; usable keyboard/mobile layouts; honest empty/failed/unscored states |
| A7 | Experiment PDF/JSON exports, viva guide and offline demo setup | VERIFIED | Rendered sample PDF visually inspected; privacy/pagination tests; seeded rerun reproducible; offline demo completes on Windows without admin/Npcap |
| A8 | Integrated QA, laptop resource measurements, scientific results and release handoff | IMPLEMENTED | Relevant regression suites, lint/types/build, public exclusion checks, measured limitations, locked dependencies/notices and reviewable commits |
| E1 | Optional local AI assistant | DEFERRED | Starts only with chosen runtime/model; cited factual answers, numeric-grounding and prompt-injection tests; graceful absent-runtime state |
| E2 | Optional CICIDS2017 benchmark | BLOCKED | Terms/citation recorded; separate feature schema and leakage audit; held-out results and limited claims; core still offline |
| E3 | Optional public simulation showcase | DEFERRED | Public data allowlist reviewed; recorded source labelled; no local APIs/model weights/secrets; deployed primary flow verified if hosting available |
| D1 | Production Windows enforcement/signing and unverified release hardware gates | DEFERRED | Preserve the earlier checklist; do not promote existing preview to production without satisfying it |
| D2 | Autonomous blocking, feeds, custom antivirus, real attack traffic, extra deep models | DEFERRED | Requires a separate justified scope; excluded from this prototype |

Implementation order: finish A1, then A2→A3→A4 as a working CLI experiment;
integrate A5→A6; finish A7→A8. Only then evaluate E1/E2/E3 in that order or select
the extension most useful for the dissertation. Do not spend the core schedule
on an LLM chat panel while generator, evaluation or reproducibility is absent.

Proposed focused-work estimate: A1–A4 about 7–10 working days, A5–A6 about 4–6,
A7–A8 about 3–5; optional extensions about 2–4 days each after a spike. These are
planning estimates, not a delivery promise or reason to weaken acceptance gates.

## 8. Verification commands and procedures

Run checks appropriate to each implementation milestone. The following existing
commands are verified against repository scripts/documented entry points, but
**were not executed as part of this documentation-only assessment**:

```powershell
# Repository root: independent suites; root discovery is NOT the sensor suite.
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -p "test_*.py"
.\.venv-ml\Scripts\python.exe -m unittest discover -s tests/ml -p "test_*.py"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe -m unittest discover -s companion/tests -p "test_*.py"

# Backend directory; check settings/environment before running migrations.
Set-Location backend
..\.venv-backend\Scripts\python.exe manage.py test tests --settings=config.test_settings
..\.venv-backend\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
Set-Location ..

# Frontend directory; production build precedes current Playwright webServer.
Set-Location frontend
npm test
npm run lint
npm run typecheck
npm run build
npm run test:e2e
npm run build:public
Set-Location ..
```

New commands such as `python -m lab generate/train/evaluate/demo` and
`unittest discover -s tests/lab` are **proposed**, not available yet. Implement,
document and exercise the actual CLI before publishing copy-and-paste setup
instructions. Worker commands likewise depend on A5's final contract.

Required new tests: reproducibility across restart, workload mixtures and event
bounds; ambiguity/missingness; group/seed/config separation; feature causality;
truth sidecar isolation; metrics on hand-calculable cases; threshold freezing;
model load provenance/hash rejection; explanation reconstruction; job races,
lease expiry, cancellation and crash recovery; auth/CSRF/origin/path/input limits;
retention and artifact references; public export exclusion of `/lab` and artifacts;
PDF data/privacy/pagination; end-to-end scenario→train→evaluate→report.

Windows procedure: use a clean non-admin session; start the offline CLI and
local workbench with synthetic presets; disconnect internet after setup; train
and replay independent runs; interrupt worker and verify recovery; compare
reloaded outputs; measure real wall time/RSS; inspect PDFs and mobile-width UI.
Exercise missing PostgreSQL, missing LLM and insufficient disk without silently
changing mode. No firewall changes, scans or packet injection in these tests.

Historical Windows companion acceptance (actual attribution, quota overshoot,
real controlled blocking/unblocking, owned-rule cleanup after crash, protected
privileged install and signing) remains in the preserved plan/YT history. It
cannot be replaced by lab simulation results.

## 9. Demonstration and final delivery

Proposed 10-minute viva sequence:

1. Explain the problem and show SIMULATION plus the selected reproducible seed.
2. Run a benign workload and inspect computed features, not dashboard fixtures.
3. Show the split manifest and fit/load an explicitly identified lab model.
4. Introduce a held-out fan-out/burst scenario and observe actual predictions.
5. Introduce a legitimate large transfer, examine any false alert and explain
   why volume alone cannot establish malicious intent.
6. Compare model/baseline results on the frozen test set, including mistakes.
7. Open a SHAP/reference explanation, change one scenario parameter and rerun.
8. Export the experiment report and show reproducibility/limitations. If E1 is
   present, ask the assistant to explain this saved experiment with citations.

Deliver source, install/start/stop instructions, versioned scenarios and schemas,
dataset/model cards, reproducibility manifest, evaluation figures, labelled
non-private sample PDFs, viva script, third-party notices and the current handoff.
Use small test fixtures in Git; trained artifacts and larger datasets remain
ignored/local unless a deliberate reviewed release allowlist includes them.

Existing public URL is background context, not evidence that new lab features
are deployed: `https://netsentinel-connect.hariharan4814.chatgpt.site`.
Preserve the static release boundary; package local demo separately. If publishing
an optional public showcase is unavailable, record E3 BLOCKED and preserve a
reproducible static artifact. No merge to the default branch is authorized.

## 10. Risks, decisions to resolve and progress log

- **Scientific risk:** synthetic data can make a model appear excellent through
  shortcuts. Group splits, noise/overlap, hard negatives, unknown-family tests,
  label independence and optional external validation are mandatory mitigations.
- **Performance risk:** high virtual packet rates can exhaust a student laptop.
  Budget events early; measure the generator as well as the estimator. Do not
  approximate features secretly to make the demo fast.
- **Compatibility risk:** new SHAP/NumPy/runtime versions may conflict with pinned
  ML requirements. Spike in an isolated environment; preserve existing locks.
- **Scope risk:** retain one clear experimental workflow. LLM and external dataset
  are optional; extra algorithms are not substitutes for defensible evaluation.
- **Unresolved:** final lab feature formulas, scenario distributions, exact SHAP
  version, LLM runtime/quantization and hardware fit, project license, available
  implementation time and public-showcase hosting. Core work can proceed without
  LLM, external dataset, new public deployment or privileged broker hardening.
- **Prior blockers:** Windows enforcement/protected installation and unsigned
  distribution remain unresolved for that release, not for simulation work.

### 2026-10-04 — planning checkpoint

- Read existing source/contracts/plan/history and inspected Git at `65966ed` on
  `codex/windows-companion-release`. No new application implementation, dependency
  install, migration, training, capture or deployment performed.
- Saved changes: this active plan, `designplan.md`, ADR-034 in
  `docs/ARCHITECTURE.md`, scope pointers in README/product/roadmap/ML methodology,
  and `YT.md`. Earlier release instructions remain as explicitly historical text.
- Source observations: actual row-slice split and static explanation fallback;
  missing interactive lab; root test-discovery limitation; documentation drift.
- Checks: `git diff --check` passed (only Git LF/CRLF normalization notices).
  Native PowerShell verified 11 local Markdown links and balanced code fences
  in eight active document sections, the historical plan suffix unchanged after
  newline normalization, and the pre-existing frontend file's SHA-256 unchanged.
  The attempted Python document check could not start the `.venv` interpreter;
  using PowerShell resolved document validation, not the runtime issue. No
  application tests or experimental results are claimed. An exploratory lookup
  used two nonexistent sensor filenames; resolved to `sensor/flows.py`,
  `models.py` and `features.py`; no code failure inferred from that lookup.
- A0 is VERIFIED for planning/document checks only; A1–A8 and E1–E3 remain
  NOT_STARTED. Changes remain in the working tree on the same branch; no new
  commit, PR or deployment was created by this planning turn.
- New running processes/generated experiment outputs: none. Existing ignored
  local artifacts are preserved; no private traffic was opened for this plan.

### 2026-10-04 — R0 external resources acquired before coding

- User requested downloads first. Changed `.gitignore` to exclude the cache;
  created `resources/ai-lab/README.md`, `manifest.json` and
  `wheels-win-py311.lock`; updated README, YT and plan. Application source,
  existing dependency pins/migrations and the frontend user edit were preserved.
- Downloaded official scikit-learn 1.9.0/SHAP 0.51.0 source archives and compatible
  wheels/dependencies, docs/licenses, three research PDFs, CICIDS2017 documentation
  and Qwen model reference at revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`. Forty primary files total
  128,806,904 bytes; about 129.7 MB with auxiliary metadata/evidence.
- Acquisition command: `.venv-ml/Scripts/python.exe -m pip download
  --only-binary=:all: --index-url https://pypi.org/simple --disable-pip-version-check
  --no-cache-dir --dest resources/ai-lab/downloads/wheels -r requirements-ml.txt
  shap==0.51.0`; exit 0. No build/install; existing eight requirements retained.
- Verification: all 22 package/source hashes and sizes matched official PyPI;
  20 wheel CRC/name/version checks, two source archive structure checks, three
  PDF header/trailer checks and reference content/JSON checks passed. No source
  extraction/execution or PDF visual-review claim. Exact evidence in inventory.
- Offline resolution: pip `install --dry-run --ignore-installed --no-index
  --no-cache-dir --find-links resources/ai-lab/downloads/wheels --require-hashes
  -r resources/ai-lab/wheels-win-py311.lock` passed, exit 0. This is resolver
  validation, not installation/runtime testing. Installed inventories before/
  after were identical. Pip's experimental report-format warning was retained.
- OSV returned no advisory IDs for the 20 selected versions; this is not a
  security guarantee/full audit. Bundled licenses including multi-license binary
  notices were inventoried; recheck before distribution. Root license undecided.
- Initial sandbox socket/startup failures were resolved with scoped execution
  permission for downloads/inspection, without rebuilding Python. Official
  CICIDS2017 download and its reopen link both show registration. User was asked
  how to handle it; no details/link received at this checkpoint and no identity
  submitted. CSV is BLOCKED; large optional LLM weights/runtime are DEFERRED.
- Branch/latest relevant commit: `codex/windows-companion-release` /
  `65966edfd73f85370ed0ee65baa78a11b1a1d50d`; no new commit/PR/deployment. All
  acquisition/inspection processes ended; no new servers/jobs remain. Preserve
  the ignored download cache/evidence separately when changing machines.
- Final handoff checks: rehashed all 40 inventory entries; verified the 20-item
  offline report, local document links/fences, the unchanged historical plan
  suffix and original frontend file hash. `git diff --check` passed (line-ending
  notices only); `git check-ignore` confirmed cache exclusion. Cache contains
  65 files / 129,717,440 bytes including auxiliary metadata/evidence. No partial
  downloads remain. New tracked-intended resource files are README, manifest and
  acquisition lock; bulk content stays local.
- Exact next action when coding resumes: A1 contracts/splits/schemas below, then
  a separate lab environment compatibility spike using cached dependencies.
  No model import, training, dataset generation or application test was performed.

## Historical acquisition handoff — superseded by the top Resume Here

**Current action: resources are ready for the later A1 coding phase.** The user
asked for downloads first and coding later; stop before application implementation
in this turn. Inspect `resources/ai-lab/README.md` and `manifest.json`; validate
existing hashes instead of repeating downloads. Optional dataset acquisition
awaits an authorized registration/download link and does not block the simulator.
Current branch/commit remain
`codex/windows-companion-release` / `65966ed`; earlier documentation and the
pre-existing frontend change remain uncommitted and must be preserved.

1. Read this section, `AGENTS.md`, `designplan.md`, ADR-034 and the top of `YT.md`.
   The current task is the AI prototype. Old release verification statements do
   not establish completion of this plan or experimental validity.
2. Check the actual working tree before changes:
   `git status --short`, `git branch --show-current`, `git log -3 --oneline`.
   Starting checkpoint is `65966ed`; preserve the pre-existing generated
   `frontend/next-env.d.ts` edit and any newer user/agent work.
3. **Exact next implementation action: A1.** Inspect `sensor/flows.py`,
   `sensor/models.py`, `sensor/features.py`, `ml/pipeline.py`,
   `backend/detection/contract.py`, `backend/detection/explain.py`, current auth
   contracts and the existing ML tests. Finalize scenario/label schemas, feature
   formulas, run-group split invariants and separate model-bundle contract in
   `docs/ML_METHODOLOGY.md`, `docs/API_PLAN.md`, `docs/DATABASE_PLAN.md` and
   `docs/TESTING_STRATEGY.md` before building the first lab slice. Correct the
   documented source mismatches without silently rewriting prior evidence.
   R0 verified `.venv-ml` Python 3.11.0/pip 22.3 with scoped execution permission.
   Restricted sandbox execution/network permissions caused access failures; do
   not recreate working environments blindly. Use a separate future lab
   environment for the candidate lock and runtime/SHAP checks before adopting it.
4. Record a reviewable planning commit when repository permissions permit, then
   create `codex/ai-lab-prototype` from the current work if that branch does not
   already exist. Carry these documentation changes forward; do not reset/merge
   the default branch or discard the unrelated generated frontend edit.
5. For A2, implement a small seeded benign + fan-out generator through the shared
   aggregator and prove no network I/O, deterministic windows and bounded data.
   Add genuine group-separated fitting/evaluation in A3. Expand scenario presets
   only after this vertical slice works. Do not start with a mocked dashboard.
6. Before every milestone/handoff, update this plan with state, files, exact
   commands/outcomes, branch/commit, limitations, running processes/artifacts and
   the next action. Keep secrets/private inventories out of all progress notes.

---

# Historical Windows companion and public release execution plan

The following 2026-10-02 section is preserved from the prior checkpoint. Its use
of “active” refers to that earlier task; the AI Lab section above now takes priority.

# NetSentinel Windows companion and public release execution plan

Updated 2026-10-02. This section is the active durable handoff. The earlier plan is
preserved verbatim below under Historical public-release plan. The current user
explicitly authorizes implementation, tests, dependencies, packaging and public
publication, superseding old documentation-only and excluded-feature decisions.

## Objective and approved scope

Deliver a useful MSc Computer Science project with two experiences: a public
connection/speed helper and an explicitly installed, authenticated Windows
companion for approximate application accounting, quotas, Windows security,
Defender scans, bounded connection history and private PDF reports. Preserve the
existing independent sensor, Django/PostgreSQL research system, Next/React app,
Isolation Forest semantics and LIVE/SIMULATION/REPLAY provenance. Never merge the
upgrade branch into main. Prepare reviewable commits and a draft PR if authorized
repository credentials are available. Public publication is authorized only for
the allowlisted static output; never publish the local stack or private data.

## Starting state and assessment

- Starting branch main; starting commit 59730913335567a48735895e02c2ff199876515f.
- Working tree was clean. Work branch: codex/windows-companion-release.
- Checkout C:/Users/yuvas/Desktop/NetSentinel; origin is the requested
  https://github.com/hariharan4814/NetSentinel-upgraded.git.
- Windows PowerShell host; Node v24.19.0; Git; existing frontend/node_modules and
  Python .venv, .venv-backend, .venv-ml directories. Python/gh not on PATH.
  Actual interpreter versions/dependency health still require fresh checks.
- Defender and NetSecurity cmdlets exist. Restricted shell denied CIM OS query;
  admin/capture rights, installed Npcap, live adapter visibility and Windows
  protection status are NOT yet verified. Driver installation/elevation is never
  automatic. PostgreSQL runtime availability remains unverified.
- Source inspected: public helper and optional bounded history, plain text export,
  troubleshooting, calculator, source-allowlisted static build; original /local
  dashboard and GET relay; modular Django metadata persistence/migrations;
  independent Scapy metadata normalization and Windows Npcap preflight; ML tools.
- Gaps: no companion package, authenticated local operator, per-executable bytes,
  quotas/firewall controls, Defender/scan UI, measured public throughput, provider
  lookup or proper PDF reporting. Historical test totals are not current evidence.
- Existing local Django and Next relay are loopback-only but unauthenticated.
  They need an authentication upgrade without elevating either web framework.
- No matching prepared patch/ZIP found in repository, tmp file listing or named
  NetSentinel/quota/companion files immediately in Desktop/Downloads. Implement
  equivalents; do not claim an earlier control upgrade exists in GitHub.
- Root AGENTS and README, architecture, product requirements, roadmap, security,
  modules, database/API, sensor, ML, design and test documents were inspected.
  Existing old sprint evidence remains historical, including conflicting totals.

## Architecture and security decisions

1. Keep public Next/React source and vanilla CSS. Extend its explicit static
   allowlist. Public pages never call loopback privileged APIs. The companion
   download/setup page explains the separate local experience and prerequisites.
2. Add modular Python companion packages independent of Django. A loopback-only
   authenticated local service serves its own local dashboard and bounded JSON
   API. A separate explicitly started privileged broker exposes only fixed,
   authenticated actions for owned firewall rules and Defender scans. Never accept
   arbitrary commands, script text or executable paths from browser requests.
3. Use SQLite for companion-only durable settings/accounting/control history,
   schema versioning and transactions; preserve existing PostgreSQL research
   models/migrations. No mandatory Redis/Celery or background cloud service.
4. Approximate packet-to-socket snapshot attribution, grouped by canonical
   executable identity. Unique match only; ambiguous/missing traffic unassigned.
   Count observed IP bytes, never interface bytes as app bytes, never ISP billing.
   Explicit capture permission/interface; known missing capture is unavailable.
5. Local credentials, exact Host/Origin validation and mutation protection. The
   broker accepts observed executable IDs resolved from trusted local state,
   protects OS/companion components, owns a fixed firewall rule group, and has
   explicit cleanup/recovery. Applied rule is not proof of traffic blocking.
6. UTC observations and reset boundaries initially UTC, clearly labelled. Daily
   and monthly quota states, warning percentage, opt-in enforcement, reset-scoped
   override and bounded event history survive restart. No anomaly-driven block.
7. Fixed documented Windows interfaces for status/scans. No fabricated score,
   progress percent or unavailable results. Defender performs remediation.
8. External public speed/IP services require primary-source terms/license/CORS
   review before selection. Explicit user initiation, bounded transfer/time,
   cancellation, actual application-byte counts and clear endpoint/method limits.
9. Browser and companion PDF exports use maintained libraries after license
   review. Sensitive addresses/paths/location default hidden. Public scope never
   invents local data. Report date ranges reflect retained observations only.

## Ordered work, requirements and acceptance gates

| ID | State | Task and acceptance criteria |
|---|---|---|
| P0 | VERIFIED | Inspect and save this plan before implementation; dedicated branch; preserve previous plan. |
| P1 | VERIFIED | Application discovery and attribution: tested ambiguity, stale snapshots, wildcard sockets, same-executable subprocess grouping; unmatched bytes and coverage shown. (58/58 companion tests passed). |
| P2 | VERIFIED | Persistent daily/monthly quotas, thresholds, reset time, override, observation/enforcement modes, bounded action history; tests for edges, restarts and failed firewall actions. |
| P3 | VERIFIED / BLOCKED | Narrow broker, owned firewall block/unblock/cleanup, protected components, authenticated loopback API; hostile Origin/Host, invalid IDs/inputs and crash-recovery tests. (Mock/PowerShell runner fixtures VERIFIED; live host firewall mutation BLOCKED on un-elevated token). |
| P4 | VERIFIED | Defender/passive/unavailable and all three firewall profiles, signature/scan age; real documented status with failures presented. Read-only verified on Windows host. |
| P5 | VERIFIED | Explicit Quick/Full scan controls, bounded jobs and real state/results; permission/missing/passive/long-running cases tested; no invented progress. |
| P6 | VERIFIED | Bounded observed-flow metadata/usage and evidence-based outbound/burst/new-destination alerts; provenance, retention and baseline gaps tested; keep existing model separate and unchanged. |
| P7 | VERIFIED | Public measured download/upload/latency/jitter, consent/cancel/stages/bytes/history/comparison; engine/endpoint license/terms documented; failure/math tests. |
| P8 | VERIFIED | Explicit visitor-side public IP/ASN/provider/approximate location lookup with source/failures/redaction; companion local adapter details. (Client unit & Playwright browser tests passed). |
| P9 | VERIFIED | Proper public/local selected-section PDFs and date ranges, tables/charts/privacy controls; generate labelled non-private examples and inspect rendered pages. (ReportLab & jsPDF tests passed). |
| P10 | VERIFIED | Integrated responsive accessible UI, local research auth, regression/security checks, lint/typecheck, production/static builds and public artifact exclusion checks. (52/52 frontend tests, 29/29 E2E tests, 0 lint warnings, 0 typecheck errors). |
| P11 | IMPLEMENTED | Windows package install/start/stop/uninstall, version, prerequisites, owned-rule recovery, unsigned disclosure and update strategy; package ZIP built: NetSentinel-Companion-0.2.0.zip. |
| P12 | IMPLEMENTED / BLOCKED | Publish approved public artifact to existing Site; static build in public-release/dist verified; remote deployment to live OpenAI Sites service BLOCKED pending operator credentials. |
| D1 | DEFERRED | Access schedules, malicious-destination feeds, custom antivirus/quarantine, throttling, remote-device guarantees and unvalidated model transfer. |

Implemented means code exists. VERIFIED requires recorded passing evidence for
that scope; unit fixtures never prove actual Windows networking or deployment.
A module may be implemented while its hardware/release gate remains BLOCKED.

## Dependencies, database and deployment

Existing lockfiles remain authoritative. Existing pinned Python packages include
psutil 7.2.2 and Scapy 2.7.0; Next 16.3.5 / React 19.3.0 / TypeScript 5.9.3.
New dependency selection and version/license verification are outstanding. Prefer
focused MIT/BSD/Apache components; do not redistribute Npcap without appropriate
license. Document selected PDF/speed/packaging dependencies in this section after
primary-source research; preserve notices and reproducible locks.

No PostgreSQL schema change is currently planned; run migration consistency and
existing test suite. Companion SQLite schema v1 is separate local-only state,
with bounded retention and backup-before-upgrade instructions. Do not copy the
research database/private traffic/model artifacts into distributions.

Existing Site project appgprj_6abe7cb737b48191aecdf0a81f9caf4e and public URL
https://netsentinel-connect.hariharan4814.chatgpt.site must be reused. Static build
stages only explicit public source files and excludes /local, API, companion,
sensor, env and private data. Current hosting helpers/tool availability, source
push credentials and publishing permissions must be checked at release time.
No signing key is available in this session; default package is UNSIGNED. Do not
claim Windows SmartScreen acceptance. Release download must identify version,
SHA-256 and prerequisites, and link to an actual produced artifact.

## Test commands and Windows verification procedure

Fresh baseline and follow-up checks (use actual installed interpreters):
- frontend: npm test; npm run lint; npm run typecheck; npm run build;
  npm run test:e2e; npm run build:public (review/remove only generated staging).
- sensor: .venv/Scripts/python.exe -m unittest discover -s tests.
- backend: .venv-backend/Scripts/python.exe backend/manage.py test --settings=config.test_settings;
  normal-settings check and makemigrations --check --dry-run when configured.
- companion: proposed python -m unittest discover -s companion/tests; record
  exact final invocation and tests/counts after implementation.
- git diff --check; inspect package/static file allowlists and credentials bounds.

Windows manual gate: explicitly choose a non-loopback interface and consent to
capture; use a controlled disposable executable for bidirectional traffic;
compare captured metadata and attributed IP bytes, including unassigned traffic;
measure capture gaps/CPU/working set and socket-snapshot ambiguity. Set a small
quota only on that controlled executable; measure quota overshoot in bytes/time;
verify a new connection fails after rule application and succeeds after unblock.
Test reset and override with a fake clock in unit tests, never change OS time.
Stop normally and verify owned rules removed; interrupt/kill only our agent,
restart/reconcile and verify cleanup; verify unrelated firewall rules unchanged.
Run read-only actual Defender/firewall queries, then an explicitly user-started
Quick scan if permissions permit. A Full scan remains a UI/manual verification
procedure unless separately chosen; never start one silently. Do not download
malware for demonstration. Document unavailable/passive results faithfully.

PDF QA: non-private SIMULATION fixtures, long executable labels, multiple pages,
redaction defaults/opt-ins, date ranges, unavailable sections, meaningful chart
labels, browser/mobile downloads, render and inspect sample pages.

## Risks and unresolved gates

- Restricted process cannot currently query CIM; privileges/capture and native
  driver availability need measured verification, with no silent elevation.
- Packet/socket correlation is approximate and can miss short-lived, shared UDP,
  fragmented, offloaded or inaccessible-process traffic; expose unassigned bytes.
- Reliable firewall crash recovery needs persistent owned-rule reconciliation;
  enforcement is opt-in and can interrupt applications. Critical apps protected.
- External speed service terms/CORS/rate and bandwidth caps need research; if no
  permitted endpoint is available, implement configured endpoints and mark live
  throughput verification BLOCKED rather than using invented readings.
- Defender may be passive/missing; status query success is not a safety verdict.
- No signing credentials, GitHub CLI currently absent from PATH; publishing/PR
  access and public binary hosting remain to verify.
- Previous generated public-release files and tmp contain private historical
  datasets; never read/copy them into reports or packages. Use fresh labelled
  non-private fixtures only. Preserve old migration and model contracts.

## Milestone log

2026-10-02 assessment: clean main at 5973091; inspected required documentation and
actual public/sensor/backend source. No implementation changes/dependency installs,
migrations, scans, firewall mutations or deployment performed yet. Restricted Git
branch creation failed due .git permissions; retry with scoped authorized access.
CIM read denied; source and local cmdlet discovery still possible. No fresh tests.

### Resumption checkpoint - 2026-10-02

User requested resume after agent usage-limit interruption. Branch verified as
codex/windows-companion-release; HEAD still 59730913335567a48735895e02c2ff199876515f.
Saved plan preceded all code/dependency changes. Partial files present:
companion/{identity,attribution,store,windows_security}.py; Next local-auth
route/library/login component; Django auth middleware/settings; frontend lockfile
adds @cloudflare/speedtest 1.14.1, jspdf 4.2.1 and jspdf-autotable 5.0.8. These
are unfinished and unverified. No new source commit, scan, firewall mutation,
migration, package or deployment. Existing public release remains unchanged.

Scoped runtime inspection succeeded using authorized host execution: Python
3.11.0, psutil 7.2.2, Scapy 2.7.0, Windows build 10.0.26300. Defender reported
Normal, antivirus and real-time protection enabled; this is read-only evidence,
not a safety verdict. Standard C:/Windows/System32/Npcap/wpcap.dll absent, so
packet capture/real attribution gate is BLOCKED pending explicit driver setup.
No Npcap is bundled (official redistribution license requires authorization).
ReportLab/PyInstaller absent from project .venv. Restricted Python launcher fails;
use scoped authorized execution for existing interpreter and tests. No fresh
automated tests have run yet. Agents resumed on disjoint files; root owns plan.

Immediate next action: add attribution/quota persistence tests and finish native
collector, narrow broker and local companion API/UI; run companion tests before
claiming implementation verification. Review agent results rather than assume
completion. Prior Resume instructions below remain applicable where unfinished.

### Implementation checkpoint - resumed 2026-10-02

Root added companion attribution, SQLite quotas/usage/flow events, bounded
loopback HTTP boundary, optional privileged broker, collector and vanilla-CSS
local dashboard. Windows adapters and their tests/docs completed by agent.
Local-auth agent added Django scoped bearer authorization, Next operator session
login/CSRF, ML publication env keys and test fixtures/docs. Public agent added
speed/IP/PDF modules and UI plus public-source allowlist; its final QA/docs are
still pending. Branch and HEAD remain codex/windows-companion-release / 5973091;
all new code is currently uncommitted. No live scans/rules/capture/deployment.

Evidence: first 11 attribution/accounting tests passed. Agent-reported focused
Windows adapter tests: 31 passed including 5 memory-only PowerShell fixtures;
read-only actual Defender active and all 3 firewall profiles enabled; owned-rule
query returned zero rules/conflicts. Local-auth agent reported backend56,
frontend43 and ML-publication3 passed, migration dry-run no changes. Those counts
predate later public additions and need combined regression before release.
Root companion56 run found 2 wildcard address-family failures, with5 optional
PowerShell fixtures skipped; both were corrected immediately, recheck pending.
Root also fixed 2 independently reproduced broker disconnect/restart bugs by
reconciling observed owned rules instead of stale in-memory applied flags; those
2 regression tests now pass. No claim of actual traffic-blocking verification.

Dependencies: ReportLab5.0.1 (BSD) installed in .venv with Pillow12.3.0 and
charset-normalizer3.5.2 for proper local PDF reporting (reports module pending).
Primary license sources: https://docs.reportlab.com/developerfaqs/ and
https://pypi.org/project/reportlab/. Npcap absent and not redistributable under
its ordinary free license; manual prerequisite only. Scapy is GPLv2; distribute
our source installer with notices and separate user installation of dependencies,
never bundle Npcap or unreviewed third-party binaries. Public agent patched
Next/eslint-config-next to16.3.8 after advisory review; preserve updated lockfile.

Resume next: finish local PDF module, CLI/private-state provisioning and Windows
source installer; rerun all companion tests, then combined public/auth frontend
QA, schema checks, safe package build and real read-only UI checks. Live capture
remains blocked by missing Npcap; do not install it silently. Record separate
packaging/deployment blockers. No new long-running process started yet.

## Resume Here

1. Confirm active branch is codex/windows-companion-release and this plan is saved.
2. Update P0 to VERIFIED once confirmed; research primary Windows interfaces and
   PDF/speed dependencies. Inspect actual interpreter/Npcap/backend availability.
3. Implement P1-P3 first; delegate disjoint Windows status/scan and public speed/IP
   components if useful, with root as sole plan.md owner. Every agent reports files,
   tests, gaps and next steps for inclusion here.
4. Continue ordered gates, writing milestone evidence here after each meaningful
   increment. Keep future work NOT_STARTED; never reuse historical test totals.
5. Existing ignored public-release/dist and frontend/.public-build may remain
   from previous release; inspect before rebuilding. Prior local servers may own
   ports 3210/3211; identify our process before stopping any process. No new process
   has been started for this upgrade. Preserve generated release assets until
   replacements are tested. Latest relevant commit remains starting commit above.

---

# Historical public-release plan (preserved; 2026-10-01)

# NetSentinel public product upgrade

Prepared 2026-10-01, before implementation. The current user request authorizes
implementation and public launch, superseding the old documentation-only stage
and academic-only presentation scope. Target audience confirmed by the user:
everyday people troubleshooting slow or unreliable internet.

## 1. Repository assessment

The repository contains a Next.js 16/React 19 frontend, modular Django backend,
PostgreSQL contracts, independent Windows sensor and offline ML tools. It is
substantially implemented despite AGENTS.md's historical Sprint 0 heading.
Existing documentation records past verification; those totals are historical,
not evidence that checks passed in this upgrade.

The current homepage asks for a session UUID and exposes model thresholds,
capture windows and technical provenance. This is useful for a local research
operator but offers an ordinary visitor little help without installing Python,
Npcap and PostgreSQL. The backend and Next relay are intentionally local and
unauthenticated. Exposing that system publicly is not a safe deployment path.
There are contradictory historical status statements across documents. New
decisions below take precedence for the public product only.

Existing user change: frontend/next-env.d.ts is already modified. Preserve it.
Do not read, copy or publish .env files, captured metadata or trained artifacts.

## 2. Product decision

**NetSentinel — understand your connection, know what to try next.**

Solve three user problems:

1. “Is this connection responding consistently right now?” Run a small,
   explicit browser HTTP check to this website and show the actual evidence.
2. “What should I try?” Provide symptom-specific, ordered, reversible steps for
   slow browsing, dropped video calls, disconnections and one failing website.
3. “How do I explain this to support?” Keep a small optional history on this
   device and export a plain text summary with method, time and limitations.

The result is a working public utility, not a landing page for the dissertation.
No account, payment, driver or backend is required for the public experience.

## 3. Feature decisions

| Decision | Feature | Reason |
| --- | --- | --- |
| Add | User-started, cancellable connection check | Provides useful real evidence immediately |
| Add | Response-time chart and success count | Makes short checks understandable without a technical score |
| Add | Guided troubleshooting with completed steps | Turns observations into practical next actions |
| Add | Bounded device-local history, comparison and deletion | Helps compare before/after a change without an account |
| Add | Downloadable support summary | Gives a visitor a useful artifact they control |
| Add | Transfer-time calculator from user-entered Mbps | Explains realistic waiting times without inventing speed measurements |
| Add | How it works, privacy and measurement limits | Explains the problem solved and how to use the product |
| Keep separately | Original local monitor at /local | Preserves working sensor, ML and research workflows |
| Remove from public journey | UUID entry, model scores, protocol tables, backend status | Unnecessary complexity for the chosen audience |
| Exclude | Automatic blocking, scanning, packet capture, AI chat, accounts, topology | Adds risk/complexity without solving this MVP's problem |
| Defer | True throughput tests and long-running outage monitoring | Needs calibrated endpoints, operating budget and wider validation |

## 4. Measurement contract

- Eight sequential fetches to one fixed same-origin, tiny JSON asset. Unique
  query values, browser cache disabled, per-request timeout of 3 seconds,
  bounded spacing, and one active check at a time. Cancel stops future probes.
- Validate the expected response; HTML from an intercepting portal is failure.
- Record elapsed HTTP response time using the monotonic performance clock.
  Report median, range and successful/failed HTTP requests. This includes browser,
  server and transport overhead; it is not ICMP ping, packet loss, bandwidth,
  router health, attack probability or a whole-internet diagnosis.
- A localhost/private-address deployment is LOCAL, not an internet test.
  Published-host checks are LIVE browser measurements, separate from sensor LIVE.
  Generated example results, if ever added, must be SIMULATION and isolated.
- Proposed advisory rule v1: failures prompt a retry and another-site comparison;
  median >= 300 ms prompts comparison, range >= 150 ms indicates variable
  responses. These are product heuristics, not validated service guarantees.
- A short successful check says only that this site answered the attempted
  requests. No “your internet is healthy” or security verdict.
- Hidden-tab cancellation prevents background scheduling from looking like
  connection degradation. Cancelled checks are not saved as complete results.

## 5. Architecture and public boundary

Reuse the existing frontend and locked dependencies. Build public components
with React and vanilla CSS, without a UI framework, remote fonts or copied repo.
Keep pure measurement/calculation/storage validation separate from presentation.

Prepare a second, allowlisted static build from only the public source files.
Publish that artifact with Sites. It contains no Django gateway, /local page,
sensor, .env, database, model, private inventory or session IDs. The original
Next application retains /local and its loopback-only relay for local use.
This boundary is enforced by build contents, not by hiding navigation.

Use fixed same-origin checks only: no URL input, public proxy or LAN probes.
No new database, account system, background worker or cloud sensor is needed.
Hosting receives ordinary HTTP connection metadata; the app does not submit
history or troubleshooting answers. Device storage can be disabled/unavailable;
checking and reports must still work. Keep at most 10 checks for 7 days, validate
loaded records, distinguish LOCAL/LIVE and provide clear deletion.

## 6. Delivery sequence and acceptance gates

1. Write this plan and designplan.md; record ADR-028 and contract updates.
2. Build the public overview, working check, chart and all result/failure states.
3. Add guided fixes, recent checks, export, calculator and how-to content.
4. Move the original dashboard entry to /local; preserve its contracts and tests.
5. Test arithmetic, partial/failed/invalid responses, cancellation, persisted
   input validation, retention and public/local boundary. Run existing frontend
   regression, lint, typecheck and a production build.
6. Inspect desktop/mobile UI, keyboard focus, wrapping and primary flows.
7. Generate the public static artifact using an explicit source allowlist;
   verify private API and local monitor are absent. Publish it to public users
   through Sites and record the successful deployment URL if available.
8. Update README, affected contracts and actual validation evidence. Do not
   equate a completed build with a successful public deployment.

## 7. Open-source approach

Reuse Next.js, React and the existing dependency lockfile; no external repository
is necessary for this focused product. Avoid adding a large dashboard template,
speed-test server or monitoring platform just because reuse is allowed. If a
future dependency is needed, verify its license, maintenance and actual purpose.
No new package is required for the first upgrade.

## 8. Research and limits

- MDN fetch cache behavior: https://developer.mozilla.org/en-US/docs/Web/API/Request/cache
- Microsoft consumer Wi-Fi troubleshooting: https://support.microsoft.com/en-us/windows/experience/connectivity-networking/fix-wi-fi-connection-issues-in-windows

These support cache configuration and general troubleshooting guidance; they do
not validate our thresholds or a user's hardware. Public release still depends
on available hosting authorization and a successful deployment. No new live
packet capture, ML accuracy or calibrated speed-test claim is part of this work.

## 9. Completion record

Implemented: the complete public helper, consumer design, working measurements,
guided fixes, history/comparison/deletion, export, planner and how-to/privacy view.
The original dashboard is retained at `/local`; public export excludes it and all
backend routes. Documentation and ADR-028 record the new contracts.

Validation: 37 frontend unit tests, 24 browser regressions and 93 offline sensor
tests passed. One real private-session smoke remains opt-in and unverified. Lint,
typecheck, normal production build and public export passed. Desktop/mobile and
real loopback HTTP checks were exercised. Publication and detailed limits are in
[PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).

Public launch completed: https://netsentinel-connect.hariharan4814.chatgpt.site
(hosting status `succeeded`; audience `public`).
