# Architecture

## ADR-028 — public connection helper and separate static distribution

**Accepted, 2026-10-01, under the user's explicit upgrade/public-launch request.**
The user selected everyday internet troubleshooting as the primary audience.
Reason: the existing academic dashboard requires private local telemetry and
technical identifiers, so it cannot serve an anonymous visitor usefully or safely.

Consequences: `/` is a public browser utility; `/local` retains the original
dashboard in the local Next application. A source allowlist produces a separate
static export containing neither the local route nor its backend gateway.
Public hosting receives only that export, never the root checkout or local env.
Native Windows capture, Django, PostgreSQL, ML and host-v1 contracts are unchanged.

Public checks use eight bounded same-origin fetches with cancellation and verified
JSON responses. Results retain browser-http-v1, timestamps and LIVE/LOCAL scope.
Browser LIVE HTTP timings are not sensor telemetry, packet loss, speed measurements
or model scores. Proposed advisory thresholds (300 ms median / 150 ms range)
are labelled heuristics. Hidden-tab checks cancel rather than recording scheduler
delay as network degradation. One check runs at a time; no URL input or proxy.

History is opt-in, browser-local, validated, capped at 10 records/7 days and
deletable. No telemetry, account, capture-control, ingestion or model endpoint
is exposed by the public distribution. The local unauthenticated stack retains
all loopback restrictions. Future cloud ingestion would need a separate identity,
authorization and privacy design; this public utility does not imply that work.

This decision supersedes earlier academic-only/cloud-excluded presentation plans
for this public slice. It does not supersede any scientific, capture-authorization
or privacy requirement. See ../plan.md and PUBLIC_RELEASE.md for implementation
and actual validation; historical evidence below is preserved.

Sprint 4 ML and detection implementation: offline dataset export/validation/training/scoring pipeline and backend model metadata + anomaly result storage.
**Sprint 4 PASS**: all frozen host-v1 feature validations, manifest checks, migrations, offline pipeline commands, API serializers, views and tests are implemented and passing.
Real LIVE model training is deferred pending collection of genuine multi-session live traffic; synthetic training data is strictly prohibited.

## ADR-025: Host-v1 offline Isolation Forest engine and detection metadata API

**Accepted for Sprint 4.**
1. **Separation of concerns**: Offline ML workflow in `ml/` operates independently via CLI. Django backend (`backend/detection/`) stores model metadata (`ModelVersion`) and anomaly scores (`AnomalyResult`), but never loads or executes pickle/joblib model artifacts inside Django request handling.
2. **Strict provenance and scientific constraints**: `LIVE`, `SIMULATION`, and `REPLAY` modes are partitioned end-to-end and cannot be mixed or relabelled. Isolation Forest anomaly scores represent negative `score_samples` (deviation from baseline), not attack probabilities. Output labels are strictly `NORMAL` or `ANOMALOUS`; labels like `ATTACK`, `MALWARE`, `INTRUSION`, `EXFILTRATION` are forbidden.
3. **Frozen seven-feature contract & eligibility**: Exact seven host-v1 features (`packets_per_second`, `ip_bytes_per_second`, `outbound_byte_fraction`, `unique_remote_peers`, `tcp_syn_fraction`, `udp_fraction`, `mean_ip_packet_bytes`) matching `sensor/features.py`. Partial, unfinalized, or corrupted windows are strictly ineligible for ML scoring.
4. **Baseline training gate**: Requires >= 5 independent whole-run sessions across >= 2 UTC dates, >= 300 train / >= 100 calibration / >= 100 test samples, >= 20% non-idle samples, and >= 2 varying features.
5. **Trusted artifact serialization**: Models are saved locally as compressed `model.joblib` bundles along with immutable `manifest.json`. Loading requires explicit SHA-256 digest match verification before unpickling.

## ADR-024: Local read-only dashboard boundary

**Continuation accepted:** the user authorized scoped GET on existing
capture-status and monitoring-sessions routes. Reuse the original recent query,
pagination and time filter via common/reads.py; add a two-field session lookup
returning one metadata object or 404. No models, migrations, ingestion semantics
or sensor changes. The relay allowlist now includes these two reads. This closes
the earlier missing-read limitation below; manual stored-data smoke now passes,
while numerical latency/continuous ingestion evidence remains deferred. Recorded capture state is shown with observed-time freshness,
and gaps remain event values, never inferred traffic or physical link state.

**Accepted for Sprint 3.** Use Next.js App Router/TypeScript in `frontend/`,
small React components and plain responsive CSS. No UI/chart/query dependency
is necessary for this bounded initial view. The browser talks to a same-origin
read-only Next route, which calls only the existing Django health, telemetry
and window GETs with a server-only loopback URL. Reason: Django intentionally
rejects browser Origin requests; preserve that boundary instead of weakening it
or adding CORS. Consequences: the relay must remain loopback-only, validate
Host/Origin and upstream paths, refuse redirects/mutations and never forward
browser credentials. This is not authentication or an externally exposed proxy.

Two-second non-overlapping polling uses cancellation/backoff and no cached
cross-session results. A five-second display freshness policy is separate from
sensor thresholds. Missing status/session read endpoints show unavailable;
neither capture state nor gap duration is inferred from telemetry. No database
schema or frozen feature contract changes are made. Those API gaps block full
Sprint 3 status integration, not the implemented read-only telemetry dashboard.

Initial Sprint 2 backend implemented, 2026-09-13: monitoring and telemetry Django
apps, DRF, environment-based PostgreSQL configuration and exactly four models.
SQLite is restricted to automated test/check tooling. Sprint 2 is PASS for the
agreed scope with operator-verified PostgreSQL 17 migrations and API persistence;
see [acceptance evidence and deferred integration](SPRINT2_ACCEPTANCE.md). This user-authorized slice explicitly
defers authentication, frontend, ML and the sensor adapter; the API is loopback-only.
The earlier broader Sprint 2/auth proposals below are superseded for this slice.
See [API contract](API_PLAN.md) and [Windows setup](BACKEND_SETUP.md).

Sprint 1 sign-off, 2026-09-12: **PASS for Ethernet 3 own-host scope**. The accepted
thirty-minute run, fresh live repeats and test-only unavailable HTTP consumer
close the evidence gates without changing production sensor code in this task.
See SPRINT1_FEASIBILITY_REPORT.md. No backend or later sprint was started.

Reduced scope accepted 2026-09-11. The four product modules are Live Network Monitor, Anomaly Detection Engine, Explainable Threat Analysis, and Network Recovery & Demo Lab. Existing Sprint 1 sensor/recovery/diagnostic code and tests are preserved; this document does not authorize new implementation.

## Components and ownership

Use one modular Django application, PostgreSQL, a Next.js dashboard, and the existing independently runnable native Windows sensor. Scapy + Npcap is the proven capture choice; do not replace working capture or install an alternative without a demonstrated need. Sensor and detection stay modular Python packages; capture and training never execute inside Django requests.

```mermaid
flowchart LR
  W[Selected Windows interface] --> S[Existing sensor and safe recovery]
  S --> C[One-second real counters and status]
  S --> A[Ten-second flow aggregation]
  SIM[Labelled SIMULATION source] --> A
  REP[Labelled compatible REPLAY source - later] --> A
  A --> F[Frozen host-v1 features]
  F --> D[Isolation Forest and feature explanations]
  C --> L[Local output]
  A --> L
  D --> L
  C --> B[Optional Django REST sink]
  A --> B
  D -->|Separate analysis stream| B
  B --> P[(PostgreSQL)]
  UI[Next.js dashboard] -->|Bounded REST queries| B
```

Sprint 2 introduces monitoring and telemetry Django apps with minimal local authentication, simple persistence and REST ingestion/read APIs. Sprint 3 adds the dashboard. Sprint 4 adds one Isolation Forest and a small detection app for manifests/results; Sprint 5 adds explanations and lab sources. These app boundaries support four modules; no incident, inventory or enterprise accounts system is required.

The model produces Normal / Anomalous and an unusualness score only on complete compatible ten-second windows. Pure explanation/rule functions describe observed feature deviations and benign alternatives. No weighted risk engine or incident correlation is required. A rule-only result has unavailable ML, never a fabricated score. The browser presents evidence and cannot capture packets or infer attack certainty.

## Runtime and contracts

The sensor owns local authorization, session UUIDs, bounded capture/queues, flow aggregation, status and feature extraction. It works without Django, PostgreSQL, a model or backend network access. It has no database credentials. Future inference is outside callbacks, with bounded processing so model errors/lag cannot block monitoring. HTTP is an optional sink, registered only for upload with a restricted source credential.

Capture callbacks normalize whitelisted metadata and enqueue it. Preserve the existing flow and host-v1 contracts, caps and two cadences; the backend adapts them into persistence without moving capture into the web application. Local JSON output is currently synchronous, so blocked output and OS calls remain timing limitations to measure.

Keep telemetry and analysis acknowledgments separate. Register session/mode/profile for upload, validate sizes/quality/versions and acknowledge only durable transactional acceptance. Retry with stable batch and record IDs. Analysis references accepted features and reports the actual trusted local model/rule versions. Incompatible analysis cannot discard valid telemetry. Backend outage uses a bounded metadata-only spool/retry policy when implemented; old-data discard is explicit and local observation continues.

Every record/view retains immutable LIVE / SIMULATION / REPLAY and source/run/session. Live baseline training uses reviewed genuine traffic for the same measurement profile. Synthetic/replayed data never enters LIVE implicitly. Simulation runs use separate session/state/credential context and generate in-memory metadata without transmitting packets. Replay preserves original event time and processing time; incompatible public feature tables remain separate offline inputs.

## Laptop runtime and update transport

The planned local stack is one Django process, PostgreSQL, one Next.js process and the existing sensor. Training and lab runs are explicit local CLI operations; diagnostic observers are opt-in existing helpers, not production services. Bind web/database access to loopback, with minimal Django session/CSRF protection and separate upload credentials; see SECURITY_RULES.md.

REST polling is the initial dashboard transport, targeting approximately one-second refresh of bounded latest samples/status. Measure latency and resource cost in Sprint 3; no Channels, WebSocket ticket or Redis dependency is assumed in Sprint 2. If push becomes necessary, record a decision and use authorized post-commit socket hints with REST reconciliation. An in-memory Channels layer requires ingestion and consumers in the same single ASGI process; external sensor/CLI processes use HTTP. No multiworker/cloud requirement.

Use local management commands/native scheduling for bounded cleanup, and trusted local CLI training/save/load/selection with a recorded actual model version. Never spawn untracked jobs from requests. Celery, microservices, enterprise reports/notifications, remote capture/job controls and cloud deployment are OUT OF SCOPE. Redis is OUT OF SCOPE unless a later measured core necessity is explicitly accepted.

## Failure behaviour

| Failure | Required behaviour |
| --- | --- |
| Missing Npcap/permissions/interface | Actionable error; genuine OS counters only when available, packet flows/features unavailable. Counters-only does not pass the packet gate. |
| Known monitored-interface loss | Immediate explicit loss/recovery status, partial old windows, bounded stop/join, revalidate original alias/GUID, refresh addresses and open new session/counter baseline. No automatic interface substitution. |
| Gap, sleep/resume or clock discontinuity | Missing coverage, never zero traffic; close/invalidate affected windows and start a compatible new epoch. No windows or rolling explanation state spanning gaps. |
| Unexpected worker error, changed GUID or failed shutdown | Explicit fatal failure; no unsafe restart or network/driver configuration change. |
| Backend unavailable | Local operation continues. Sprint 1 proves this with a test-only bounded HTTP mirror and explicit counted discards; future production spool/retry/delivery still needs integration validation. |
| Stale sensor / lost browser connection | Last-observed time and unknown current traffic; REST retry/backoff and authoritative refresh. |
| No model or incompatible/partial feature | Continue collection; ML unavailable/unscored. Valid observed idle may score later; capture absence may not. |
| Queue/flow/disk pressure | Preserve caps, count loss, mark coverage/partial state and reject ingestion visibly if storage cannot recover. |
| No anomalies | Useful rates, packets, protocols, flows and history; no secure-network verdict. |
| Post-NAT/unknown attribution | Host/interface aggregate only; no remote-device traffic claims or device scores. |
| SIMULATION/REPLAY unavailable | Explicit unavailable lab state; no prefilled findings or synthetic LIVE fallback. |

Recovery defaults and all Sprint 1 numerical gates are unchanged. Historical
termination cause remains unproven; subsequent recovery cleanup, accepted
uninterrupted stability and fresh clean exits support the scoped Sprint 1 PASS.
See SPRINT1_FEASIBILITY_REPORT.md for the evidence and qualifications.

## Decision register

ADR-023 - **Accepted for the initial Sprint 2 scope, 2026-09-13:** two Django
apps with MonitoringSession, TelemetrySample, TrafficWindow and CaptureStatus
only. Reason: implement the user's minimum persistence/API task without changing
the proven sensor. Consequences: aggregate typed fields only, UUID identities,
UTC event/receipt times, immutable session provenance, normalized content digests
and unique keys for retry/conflict handling. PostgreSQL transaction advisory
locks serialize registrations sharing a run ID, including first registration;
source/mode/interface/profile must agree across recovered sessions. Actual
PostgreSQL concurrency testing remains pending local installation.

The user's explicit no-authentication instruction supersedes earlier required
auth/enrollment work for this slice. Loopback peer and fixed Host checks reject
remote requests; Origin/cross-site requests are rejected. This is not protection
against another local process. No proxy/deployment or frontend is supported yet.
The root .env supplies required runtime secrets/database settings; the independent
.venv-backend pins Django 5.2/DRF/psycopg without touching sensor dependencies.
No SQLite fallback at runtime. Test settings reject runtime commands.

Only single-record ingestion and bounded recent reads are implemented. No packet
payload, per-flow inventory, embedded features/models or ingestion-receipt table.
Digests live on the four records; retries are idempotent while records are retained.
Explicit pruning removes at most 1000 expired rows per telemetry/status table per
invocation after 24 hours by receipt time, retaining session manifests. Automatic
retention, global row/byte admission budgets and production sensor upload/spooling
remain deferred; this does not claim the former larger storage/transport gate.

ADR-022 - **Accepted for Sprint 1 evidence only, 2026-09-12:** attach a test-only
optional HTTP health mirror at the existing sensor emission boundary. Reason:
the old preflight-exception test could not prove local operation during an HTTP
outage. Consequences: actual POST to a reserved non-listening loopback endpoint,
0.2-second socket timeout, local flushed output first, one attempt followed by
an open circuit, no queue/retries, and counted undelivered copies. Live controlled
TCP/UDP and windows continue after failure. No production sensor/client/service
or ingestion schema is added. Future transport durability/reconnect/security
requires its own authorized implementation and integration evidence.

ADR-021 - **Accepted, 2026-09-12; live cadence validation passed:** anchor
capture health deadlines to each session's monotonic origin, separately from
the last actual counter measurement. Reason: the official 1,800-second run
emitted only 1,669 valid samples because collection overhead accumulated after
each one-second wait. Consequences: retain actual elapsed-time rates, skip
missed deadlines without synthetic catch-up records, reset cadence with each
recovered session, and preserve all failure/recovery and acceptance thresholds.
Synchronous OS/output delays remain possible; the full repeat passed with 1,799
valid samples, all checks true and exit 0.
Evidence and offline regression are in SPRINT1_FEASIBILITY_REPORT.md.

ADR-019 — **Accepted, 2026-09-11: reduced academic scope.** Reason: deliver a clearer, defensible M.Sc. project using proven Sprint 1 work. Consequences: four core modules, seven sprints numbered 0–6, no incident/risk/enterprise feature delivery, no sensor/test rewrite, and all S1-01–S1-08 gates remain mandatory. Sprint 2 is backend-only; Sprint 3 is dashboard; Sprint 4 is one Isolation Forest; Sprint 5 is feature explanations and labelled labs; Sprint 6 is integration/evaluation/submission. Basic authorization, metadata privacy, provenance, retention and genuine measurement remain required. Replaces older roadmap tiers and incident/demo policy; historical evidence is retained.

ADR-020 — **Accepted planning choice, 2026-09-11; performance validation pending: REST first and minimal local access.** Reason: a single-operator laptop needs simple telemetry APIs before push/auth orchestration. Consequences: Django session/CSRF and separate source credentials are the starting access design; one-second bounded polling is evaluated in Sprint 3. ADR-005's PostgreSQL durability remains; its required socket transport and ADR-006's mandatory ASGI/Channels setup are superseded. Single-process restrictions still apply if Channels is later justified. No Redis unless necessity is demonstrated and separately accepted; no Celery or cloud requirement. No security or latency pass is claimed.

Decisions 001–018 below retain the original Sprint 1 reasoning. Earlier device-model, browser-job and socket proposals are historical or conditional under ADR-019/020, not active deliverables.

ADR-018 — **Accepted for opt-in diagnosis only**: use a separate local diagnostic
observer to record native process exit independently of the capture interpreter,
plus private fault-handler and lifecycle text logs. Reason: the USB recovery run
ended without Python finalization. Consequences: extra process only for explicit
diagnostics, no automatic restart, no memory/payload dumps, no new production
service or acceptance relaxation. Observer timeout/cancellation is recorded
before stopping its own child tree; loss of both observer and child can still
prevent terminal evidence. This is instrumentation, not a proven native fix.

ADR-017 — **Accepted for local Sprint 1 implementation; live recovery validation
pending**: supervise independently bounded capture sessions on known interface
loss. Reason: a reproduced Wi-Fi down-state exception should expose missing
coverage and permit conservative recovery. Revalidate the same alias/GUID and
refresh addresses; close partial windows and reset counters/aggregation under a
new session UUID linked by run ID. Consequences: gap status must never become
valid zero traffic; summaries span sessions but features do not. Any gap prevents
uninterrupted stability acceptance. Retry defaults are 2 seconds / 30-second
maximum per loss, configurable within hard limits and the finite run duration.
Unexpected exceptions and failed worker shutdown remain fatal. Synchronous
OS/output calls limit guarantees about wall-clock cancellation; no network
configuration changes, extra services or background recovery workers are added.

Sprint 1 continuation ADR-016: freeze host-v1's seven reconstructible values and
add local resource/counter telemetry plus finite opt-in validation scripts. This
permits evidence collection without any web/model dependency. Retain selected
address context for reconstruction; protect it as private metadata. Late drops
invalidate remaining session windows conservatively. A separate same-device
reference parser checks accounting but cannot detect shared Npcap/offload blind
spots. **Accepted for Sprint 1 implementation; hardware validation pending**.
Reasons: close feature/reliability evidence gaps without enlarging the MVP.
Consequences: synchronous output latency and missing HTTP-sink integration remain
explicit limitations; kernel loss remains unknown. Full gates still precede web work.

| ADR | Decision | Reason and consequence | Status |
| --- | --- | --- | --- |
| 001 | Modular Django monolith plus local sensor | Clear privileges and ownership without many services | Accepted |
| 002 | Metadata/flow persistence, no payload by default | Reduces privacy and storage burden; limits content-based conclusions | Accepted |
| 003 | Isolation Forest plus separate interpretation | Scientific honesty; requires independent rule evaluation | Accepted |
| 004 | Provenance partition in every pipeline stage | Prevents demo/replay contamination; adds contract checks | Accepted |
| 005 | PostgreSQL plus post-commit socket hints | Simple durability; REST reconciliation required | Accepted durability; required sockets superseded by ADR-020 |
| 006 | Single ASGI process before Redis | Laptop simplicity; cannot scale workers with in-memory messaging | Conditional only if push justified; ADR-020 |
| 007 | Offline training, sensor-local inference | Keeps requests fast; requires trusted artifact distribution and version handshake | Accepted |
| 008 | Scapy-first capture spike, PyShark alternative | Scapy 2.7.0 with Npcap 1.88 demonstrates Phase 1B host capture; PyShark is unnecessary for this evidence. Sustained overhead remains to measure. | Accepted for Phase 1B |
| 009 | Host/interface-first observation | Remote-device attribution cannot be assumed from discovery/NAT; device models are OUT OF SCOPE under ADR-019 | Accepted |
| 010 | Independent sensor and two publication cadences | Useful without backend/model; real samples every second, findings from finalized 10-second windows | Accepted |
| 011 | Shared feature compatibility gate | Dataset column names alone do not establish live compatibility | Accepted |
| 012 | Local CLI controls/lab launch before browser jobs | Avoids an undocumented task queue and remote privileged execution in MVP | Accepted |
| 013 | Early age/row/disk telemetry budgets | A bounded capture queue does not bound PostgreSQL growth | Accepted |
| 014 | Phase 1A psutil-only runtime; fail-closed capture preflight | Npcap was absent during Phase 1A. Pin tested psutil 7.2.2 on Python 3.11.0; pure metadata fixtures prove aggregation only. | Historical Phase 1A; capture portion superseded by ADR-015 |
| 015 | One selected Npcap interface, Scapy AsyncSniffer and metadata-only queue | Phase 1B verifies Windows alias-to-index and Npcap mapping, store=False, non-promiscuous IP filter, callback normalization and independent timer-driven aggregation. Driver is manually installed. Queue/parser loss conservatively invalidates remaining session windows; kernel loss stays unknown. CLI prints summaries only; packet objects/payloads are not persisted. | Accepted for Phase 1B; full Sprint 1 remains partial |
| 025 | Offline Isolation Forest & detection metadata API | Offline CLI, strict 7-feature contract, 5+ run baseline gate, metadata-only Django app | Accepted |
| 026 | Lightweight feature explainability & Light Theme UI | Deterministic baseline reference quantile evaluation without LLM/SHAP; dynamic DRF serializer; light theme design with Roboto typography | Accepted |
| 027 | End-to-end demonstration readiness & viva defense | Complete integration verified against genuine LIVE Session 4 (score ~0.7314, threshold ~0.7191); viva defense guide created | Accepted |

All sprints 0 through 6 are complete, operator-tested, and verified against genuine LIVE data. Evidence is documented in respective sprint acceptance reports and [VIVA_GUIDE.md](VIVA_GUIDE.md).
