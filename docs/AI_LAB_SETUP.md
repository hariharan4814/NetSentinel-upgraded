# NetSentinel AI Lab: setup and demonstration

This is a local M.Sc. research prototype. It generates virtual **SIMULATION**
packet metadata, aggregates the original seven host-v1 features, fits actual
models, evaluates held-out runs and explains predictions. It sends no generated
traffic onto your network. It needs neither Npcap nor administrator privileges.
An unusual sample is not evidence of malware or an attack.

## Setup on Windows

Reference platform: Windows x64, Python 3.11, Node.js 22 or newer. The existing
sensor, backend and ML environments remain separate. From the repository root:

```powershell
py -3.11 -m venv .venv-lab
.\.venv-lab\Scripts\python.exe -m pip install --require-hashes -r requirements-lab.lock
py -3.11 -m venv .venv-backend
.\.venv-backend\Scripts\python.exe -m pip install -r requirements-backend.txt
cd frontend
npm ci
npm run build
cd ..
.\.venv-lab\Scripts\python.exe scripts/run_ai_lab.py
```

Skip environment creation/installation when already prepared. To install from
the verified resource cache without internet, append `--no-index --find-links
resources/ai-lab/downloads/wheels` to the lab pip command. The lab lock contains
Windows CPython 3.11 wheel hashes; it is not a cross-platform lock.

Choose a local password of 32–256 printable characters without spaces when
prompted. Use that password in the opened browser. It is not printed or written
to a configuration file. Alternatively, supply `NETSENTINEL_OPERATOR_PASSWORD`
in your environment; never commit it. The launcher makes separate random API
credentials each time, binds both servers to loopback, migrates only the separate
lab database, and starts the ML worker. Do not run the launcher as administrator.

Open `http://127.0.0.1:3105/lab`. The API uses port 8811. Use
`--frontend-port` / `--backend-port` for occupied ports; the launcher never kills
unrelated services. `--no-browser` suppresses opening a tab. Ctrl+C stops owned
processes. An interrupted job becomes failed after its lease expires when the
queue is next accessed; it is never reported as successful.

The standalone runtime explicitly selects `config.lab_settings`: SQLite stores
only experiment jobs in `artifacts/lab/standalone/demo.sqlite3`. Worker artifacts
are below the same directory. These outputs are ignored by Git. Original
`config.settings` still requires PostgreSQL for the research monitor. Running
this demo does not verify PostgreSQL, LIVE capture or Windows enforcement.

Retained jobs are bounded to 20 terminal records. The worker separately bounds
its owned directories and disk budget. Shutdown preserves results. To remove
demo data, first stop the launcher and remove only its `artifacts/lab/standalone`
directory. No firewall rules, drivers or Windows security settings are changed.
This source launcher is unsigned; no installer or SmartScreen claim is made.

## Viva demonstration

1. Explain the problem: repeatable study of network deviations without generating
   real attacks or presenting unexplained scores as security verdicts.
2. Sign in, choose a seed and scenario settings, then start an experiment. The
   progress stages come from the running worker, not a timed animation.
3. Inspect benign routine/bulk traffic and challenge fanout/SYN/UDP patterns.
   Replay advances through already computed held-out windows; it is not LIVE.
4. Compare Random Forest against dummy and rule baselines. Explain a confusion
   matrix, a false positive and a missed challenge. Results vary by seed/noise.
5. Explain that Isolation Forest was fitted on benign training data, with its
   threshold calibrated on benign validation data; its score is not probability.
6. Inspect SHAP contributions for the classifier. References come from training
   data. Contributions explain this fitted model, not real-world causal effects.
7. Download the semantic PDF and show its scope, gaps, metrics and limitations.
8. Repeat the seed to demonstrate dataset reproducibility; increase noise and
   compare measured outcomes. Cancel a larger run and restart the application to
   demonstrate persistence and interruption recovery.

## Independent CLI and scientific evaluation

```powershell
.\.venv-lab\Scripts\python.exe -m lab demo --out artifacts/lab/my-demo --seed 42
.\.venv-lab\Scripts\python.exe -m lab inspect artifacts/lab/my-demo
.\.venv-lab\Scripts\python.exe -m lab benchmark --out artifacts/lab/my-study --seeds 42 43 44
.\.venv-lab\Scripts\python.exe -m unittest discover -s tests/lab -p "test_*.py"
.\.venv-lab\Scripts\python.exe scripts/verify_ai_lab.py
```

Use a fresh output directory for each run. Models are local trusted artifacts;
never load a model file from an unknown source. The benchmark reports repeated
seeds, whole-run bootstrap uncertainty and an excluded-family study. It is
separate from the browser result schema. Synthetic accuracy cannot establish
performance on real attacks. See `ML_METHODOLOGY.md` for the protocol and limits.

The integration script uses new ignored storage, ephemeral credentials and
actual HTTP services/worker. It checks access controls, real completion, cancel
and restart persistence; it does not replace browser/PDF or PostgreSQL testing.
Current verified results and exact outstanding work are recorded in `plan.md`.

## Failure diagnosis

- Startup requires an existing production frontend build. Rebuild after source
  changes. Do not use Django's test settings to serve the app.
- A pending job requires the worker. Failed/expired jobs are explicit records;
  fix the cause and create a new run instead of relabelling them successful.
- A missing dependency requires the correct separate environment. Original ML
  models and lab models have different contracts and cannot be interchanged.
- Local sign-in expires after four hours and after a server restart. Re-enter
  the password chosen for the current launcher session.
- The public static export intentionally has no local lab APIs or private data.
  It cannot train models or control an installed companion.

This prototype uses scikit-learn (BSD-3-Clause), SHAP (MIT), the existing
Django/Next/React stack and jsPDF tooling. The pinned external inventory and
upstream license texts are described in `resources/ai-lab/README.md`. Redis,
Celery, remote LLM services and paid APIs are not required.
