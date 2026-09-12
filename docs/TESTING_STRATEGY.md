# Testing strategy

## Final Sprint 1 acceptance - 2026-09-12

**93/93 tests passed in 4.295 seconds**, exit 0, with
`.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`.
`git diff --check` passed. Four new offline HTTP failure tests open no sockets:
local-first delivery/record preservation, refusal/timeout/HTTP failure without
retries, HTTP 503, unexpected success classification and local-output errors.
Existing sensor/recovery/feature/stability tests are retained.

Separate explicitly authorized live processes passed controlled TCP/UDP and
window/feature generation. `manual_live.py --interface "Ethernet 3" --http-outage`
then demonstrated a real HTTP timeout with 22 subsequent flushed local health
records, four windows and captured controlled TCP/UDP, no retries/queue or
application loss. Upload discards are explicit. This is a test-only optional
consumer at the real emission boundary; future production delivery semantics
are not certified. No backend was started or production sensor changed.

The accepted thirty-minute log, operator idle confirmation, memory trajectory,
matched TCP evidence and historical recovery review are in the
[final feasibility matrix](SPRINT1_FEASIBILITY_REPORT.md). Sprint 1 is **PASS
for Ethernet 3 own-host scope**; no threshold changed and no later sprint starts.
Older counts and open-evidence statements below describe their dated work.

## Sample cadence verification - 2026-09-12

Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`
**89/89 passed in 4.132 seconds**, exit 0; `git diff --check` passed. Three new
tests cover accumulated collection/output cost over 1,800 virtual seconds,
long-stall invalidity without catch-up records, and the unchanged sample-count
and all-valid predicate. The cadence regression failed before the sensor fix
(1,694 samples) and passes after (1,799); these are offline fixture results.
Existing recovery, privacy, process-diagnostic and feature tests all pass.
No live rerun was performed. The inspected official run remains failed at
1,669/1,700 required records and must be repeated with the updated scheduler.
See [the latest investigation](SPRINT1_FEASIBILITY_REPORT.md) for the full-log
audit, exact command, operator reviews and remaining gates. No threshold changed.

## Scope-cleanup verification — 2026-09-11

Ran the full existing suite with `.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`: **86/86 passed in 2.657 seconds**, exit 0. The suite's missing-driver/stop messages are expected injected paths. Unit discovery opens no live capture and sends no controlled network traffic. All existing sensor, test and dependency files are preserved.

No hardware diagnostic, thirty-minute run, Django/PostgreSQL/Next.js or model validation was performed in this cleanup. Formal Sprint 1 remains PARTIALLY PASSED / NO-GO. SHA-256 comparison against the starting working tree confirms every existing non-document file (including untracked sensor/tests and dependencies) is unchanged; no new tracked/unignored files were added. All eight Sprint 1 gate rows and the live feature contract are unchanged. Historical feasibility/review evidence is retained. All 46 local Markdown links resolve. `git diff --check` passed, exit 0, with Windows LF/CRLF notices only.

## Historical Sprint 1 verification log

The dated counts and "untested"/adapter statements below describe their original runs, not today's hardware state. The latest feasibility report governs unresolved live evidence. No existing test or acceptance threshold is removed.

Latest verification: **86/86 tests pass in 1.609 seconds**, including seven new
process/lifecycle diagnostic tests. `git diff --check` passes. The observer CLI
was also exercised with an intentionally nonexistent interface: child exit 2,
validation_error and normal process markers were retained; no capture opened.

Process-termination diagnostics: disposable offline child processes test normal
exit, SystemExit(-1), and deliberate os._exit(-1) **only in the test child**.
The latter validates independent exit evidence when every finalizer is bypassed;
it does not reproduce or explain the real USB termination. Tests also cover
thread BaseException reporting without thread/packet retention, signed/unsigned
Windows status, explicit observer-timeout intervention, and capture lifecycle
breadcrumb ordering across recovery. No native crash/memory dump is induced.
Previous hardware recovery successes remain partial evidence; the abrupt exit
requires another instrumented diagnostic before clean acceptance.

Verification follow-up: **79/79 tests pass in 1.088 seconds**. Rechecking on the
current network exposed implicit Scapy MAC resolution in the shared `decoded()`
fixture (`Ether()` lacked source/destination MACs). The first rerun was stopped
after resolution attempts and a background-thread exception; it is not a passing
result. Fixtures now use explicit synthetic locally administered MACs, with a
regression forbidding IPv4 MAC resolution. The subsequent full suite passed
without those warnings or background exceptions. Capture/recovery logic and
acceptance thresholds were unchanged by this fixture correction.

Interface-loss follow-up (2026-09-09): **78/78 tests pass** (17 new tests over
the diagnostic baseline); `git diff --check` passes. `test_recovery.py` exercises the real
capture lifecycle with a virtual clock, mocked interface/driver/counters and
permitted metadata only. Coverage includes down/missing classification, recovery
and timeout, exact retry spacing, original run deadline, address refresh/counter
baseline reset, session separation and partial windows, no gap samples, later
fully observed idle windows, replacement GUID rejection, unexpected ValueErrors,
shutdown failure, Ctrl+C/requested cancellation and slow revalidation exceeding
the deadline. `test_stability_live.py` also prevents recovered or explicitly
diagnostic runs from being accepted as clean uninterrupted stability. Default
recovery parameters are implementation choices, not revised acceptance targets.
Live recovery remains untested; the feasibility report gives an eight-minute
diagnostic command. A real interface-loss gap still requires a new uninterrupted
30-minute acceptance run from zero.

Wi-Fi diagnosis follow-up (2026-09-09): **61/61 tests pass** after the diagnostics
change. `test_stability_live.py` adds ten offline
checks for diagnostic retention, worker errors, phase boundaries, malformed
aggregation, statistics/preflight failures and virtual capture/controlled traffic.
These fixtures open no capture device and send no traffic. The user-reported
367.172-second failure has **not been reproduced**; its original traceback was
discarded by the old harness. See the feasibility report follow-up. Exception
logging now preserves messages/tracebacks without frame locals. Full Sprint 1
acceptance still requires a fresh 30-minute run after the cause is established.

Sprint 1 continuation: **51 unit tests pass**. `test_completion.py` adds contract
arithmetic and deterministic resource/failure coverage; fixtures transmit nothing.
Explicit-only scripts `stability_live.py` and `tcp_reference_live.py` prepare the
remaining live gates. Both are currently blocked by the missing Ethernet 3 adapter;
do not call preparation a hardware test pass. The prior Phase 1B counts below are
historical. See the current feasibility report for commands and observed failures.

This document plans future verification. No tests, environments or application checks were implemented or run in Sprint 0. Keep tests focused on consequential behaviour, independent expectations and failure modes rather than mirroring implementation.

Phase 1B now has 32 sensor unit tests (`python -m unittest discover -s tests/sensor -v`) and an explicitly invoked `tests/sensor/manual_live.py --interface <alias>` hardware check. The latter sends one public HTTP HEAD and one DNS query from the selected local IPv4 address during bounded capture; it is never part of unit discovery. Unit fixtures transmit nothing. Evidence and remaining full-sprint gates are recorded in [SPRINT1_FEASIBILITY_REPORT.md](SPRINT1_FEASIBILITY_REPORT.md).

## Layers and future acceptance evidence

| Layer / sprint | Critical checks |
| --- | --- |
| Existing sensor / Sprint 1 | Preserve all metadata/aggregation, feature arithmetic, capture lifecycle, recovery, process-diagnostic and stability tests. All S1-01–S1-08 hardware/privacy/timing gates remain unchanged. |
| Backend / Sprint 2 | Actual PostgreSQL migrations/constraints, bounded ingestion and reads, atomic idempotency and changed-payload conflict, source/mode authorization, session registration, status/gap preservation, retention and backend-outage independence. |
| Dashboard / Sprint 3 | Genuine one-second telemetry, distinct ten-second flow cadence, units/protocol/flow-count semantics, stale/gap states, mode/run cache separation, polling retry and measured display latency with zero anomalies/no model. |
| Isolation Forest / Sprint 4 | Frozen host-v1 reconstruction parity, train-only preprocessing, whole-session chronological split, trusted save/load, score direction and threshold boundary, actual model versions, deterministic seed, incompatible/incomplete/no-model rejection without losing telemetry. |
| Explanations / Sprint 5 | Observed value/reference/units, bounded rule context and reset on gaps/splits, benign alternatives, unavailable evidence, no unsupported attack label, no automatic blocking. Derived port/flow counts cannot silently expand host-v1. |
| Demo/replay / Sprint 5 | Deterministic generated metadata through shared aggregation/rules; permanent provenance and separate state. Compatible replay timing/extraction and parser/privacy checks if implemented; otherwise explicit unavailable status. |
| Final integration / Sprint 6 | Authorized sensor to database to dashboard with no model/zero anomalies; analysis and explanations on compatible windows; recovery gaps; repeatable labelled demo; local startup/restore, accessibility, resource/stability and report evidence. |

## Fixtures and provenance

Keep existing synthetic packet/metadata fixtures offline and hand-calculated. Never modify test expectations to hide sensor failures. Preserve exact count checks, 1e-12 feature fraction tolerance, half-open windows, two-second lateness, null/idle distinctions, fragments/unknown direction and bounded losses. Mode/run IDs and scenario labels never become predictive inputs.

Future API/DB/UI checks must reject mixed-mode records and cross-session evidence, attempted LIVE session rebinding, lab credentials accessing LIVE uploads, stale mode responses and incompatible model profiles. Local endpoint tuples do not become device identities. Gateway/NAT examples must not yield fabricated remote-device bandwidth or connection-count claims.

Run the ML_METHODOLOGY.md demo twice with fresh state: benign at most three outgoing ports yields zero qualifying windows; each of two complete windows with 24 outgoing destination ports to one peer yields a computed rule finding at the provisional threshold 20. With ML disabled, score/label remains unavailable. Retried delivery creates no extra findings. Never seed scores or findings. This replaces the historical risk-55/one-incident fixture; it does not change any existing Sprint 1 test.

Public-data compatibility checks reject matching column names with wrong byte/direction/window/header semantics. Compatible PCAP fixtures require explicit provenance/label mapping and extraction parity, not merely successful decoding. Use only tiny generated temporary replay captures; clean them up. Private captures/datasets/models stay out of Git.

## Research evaluation

Evaluate one Isolation Forest under ML_METHODOLOGY.md's reviewed genuine baseline, chronological session grouping, calibration/test separation and locked manifests. Report explanation/rule correctness separately; complex multi-model and weighted-risk comparisons are OUT OF SCOPE.

Define the evaluation unit and positive-label meaning first. Distinguish labelled controlled scenarios, unlabelled LIVE observations and SIMULATION/REPLAY evidence. Precision/recall/F1 require suitable labels; recall with no positives is undefined and PR-AUC requires a meaningful ranking and both classes. Report reviewed false anomalies per observed benign hour, ordinary bursts, coverage/unscored time, independent-session variation and small-sample limits. Unreviewed live anomalies are not automatically false alerts or attacks.

## Performance and resilience

Sprint 1 follows ROADMAP.md S1-01–S1-08 exactly. Require the full 1,800-second uninterrupted run, idle/controlled phases, actual working set below 500 MiB, CPU/queue/flow/loss/timing evidence, matched TCP within 5%, UDP correctness, end-to-end shutdown within five seconds, privacy and fresh-process repeat. Recovery or a diagnostic run cannot satisfy uninterrupted clean capture. Unsupported hotspot/monitor/remote visibility can remain documented without adding those features.

Existing validator checks also remain unchanged: at least 1,700 valid samples, at least 55 successful controlled HEAD requests and no traffic errors, p95 flushed-console delay at most two seconds, p95 processing after lateness at most one second, caps 20,000 queued records / 10,000 flow entries / two windows, conservation and no unexplained loss/error. Operator review of idle phase and memory trajectory is required. These are preserved validator coverage assumptions, not new tolerances.

After integration measure p95 one-second sample-end-to-display and finalized-window-to-display latency separately (proposed below three seconds each). Record actual CPU/RAM/disk/throughput/loss and final shutdown. Pressure fixtures test caps; they do not prove remote-device visibility or maximum sustainable database capacity.

Use 100,000 flow rows for initial reads and near-budget writes/cleanup with measured table/index/WAL growth. Test DATABASE_PLAN.md age/row/byte thresholds, status availability under pressure, receipt integrity, coverage on expiry, disk reuse and restore. No incident snapshots or enterprise reports are required.

Inject unavailable HTTP sink, disconnect/restart, disk pressure, malformed batches,
stale clocks, invalid models and credential revocation as applicable to each
authorized sprint. The old `test_unavailable_backend` injects a preflight exception
and is not HTTP evidence. S1-05's actual outage gate is now covered by the opt-in
live HTTP mirror above, with continuing local collection/output and counted
undelivered copies. Future production ingestion/retry/spool integration still
needs its own tests; retries retain source IDs and delayed data cannot look current.

If Channels is later justified, add auth/origin/expiry/revocation tests, post-commit event publication and missed-event REST reconciliation in the chosen single-process runtime. WebSocket/Redis infrastructure is not needed for initial REST-only delivery.

## Security and manual checks

Test minimal operator session/CSRF/origin restrictions, source credential scope/revocation, object-ID substitution, cross-mode access, bounded queries/uploads and secret redaction. Check trusted model origin/digest, replay path traversal/parser quotas if supported, and UI escaping. Inspect library/log/spool/temp outputs for payload retention. Backend revocation denies uploads but cannot promise immediate offline capture shutdown.

Record Windows OS/adapter/driver/access/mapping for every claimed supported capture profile. Manual live checks are opt-in and separate from unit discovery. Do not run hardware/long tests merely for a documentation change. Test keyboard navigation, screen-reader basics, responsive layout and projector readability on the four core views.

## Delivery gates and exclusions

Each authorized sprint supplies relevant tests, reproducible steps and honest limits; database work requires migrations and real PostgreSQL checks, dashboard delivery requires a production build, and final delivery requires end-to-end/privacy/provenance validation. Do not invent passes for unimplemented capabilities.

Advanced RBAC, incident/risk/notification workflows, broad inventory, topology, Bluetooth, LLM/intelligence integration, multi-model comparisons, enterprise reports, remote control/jobs and cloud/microservice tests are OUT OF SCOPE. All existing Sprint 1 tests remain required. Final submission is Sprint 6, with real monitoring, a separately labelled safe demo, measured evaluation and disclosed unsupported capabilities.
