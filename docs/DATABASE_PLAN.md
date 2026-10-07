# Database plan

## AI Lab persistence — implemented 2026-10-05

`experiments.ExperimentJob` stores UUID identity, status/stage, UTC creation/update
times, normalized bounded configuration, cancellation request, nullable progress
counts, a fixed redacted failure description, bounded result JSON, a SHA-256 lease
digest and lease expiry. Only SUCCEEDED rows can contain results; a conditional
unique constraint permits one RUNNING job. Progress cannot exceed its total.
Model artifacts are files in an owned ignored directory, never Django blobs or
LIVE model registry entries. Index `(status,created_at)` supports admission/claim.

`experiments.QueueGuard` is a singleton row (`id=1`). Three additive migrations
create jobs, create the guard and seed it. Normal research runtime applies these
to PostgreSQL with the original migrations preserved. PostgreSQL queue actions
use an advisory transaction lock. Explicit `config.lab_settings` installs only
`experiments` and uses a separate SQLite file; its guard UPDATE is the first
statement in the transaction to serialize writers before reading queue state.
This mode is an intentional runtime option (ADR-035), not automatic fallback.

Admission permits four QUEUED jobs alongside one RUNNING job, retaining at most
20 jobs by pruning oldest finished rows in `(created_at,id)` order. Active jobs
are never evicted. A worker must renew its 30-second lease; expired jobs fail
as interrupted on the next queue operation. Config/result bodies are validated
and bounded, but the row cap does not automatically shrink the SQLite file. Back
up or remove the separate lab database only while its processes are stopped.

Temporary SQLite migration, concurrent admission/claim and a second-process
persistence/recovery test pass. This is not PostgreSQL verification: the original
local PostgreSQL service is unavailable and its data directory was preserved.
Apply and verify new migrations there when the service is restored. Historical
four/six-model descriptions below refer to their dated research milestones.

## Implemented initial Sprint 2 slice - 2026-09-13

Exactly four models now exist: `monitoring.MonitoringSession` and
`monitoring.CaptureStatus`; `telemetry.TelemetrySample` and
`telemetry.TrafficWindow`. See [API_PLAN.md](API_PLAN.md) for fields and validation.
The initial task defers Sensor, Interface, users, receipts and per-flow tables
from the broader proposal below. Source UUID/interface/mode/run/profile live on
the immutable session; child rows reference it. Typed samples retain cumulative
OS counters, nullable deltas/rates, elapsed time, validity and reason. Windows
retain aggregate directional/protocol counts, IP bytes, quality and timestamps;
there is no packet payload, arbitrary JSON or feature/model blob.

Three existing generated migrations are retained: monitoring/0001_initial,
telemetry/0001_initial and telemetry/0002_trafficwindow_window_session_end_idx.
They supply foreign keys, UUID/observation uniqueness, conservation/validity
checks, and session/time indexes. Digests on retained rows implement idempotency;
no extra receipt model is needed. Django's own migration bookkeeping is separate
from the four application models. Runtime is PostgreSQL only; SQLite is confined
to automated tests/checks. The operator verified all three migrations and API
persistence on PostgreSQL 17; see [Sprint 2 acceptance](SPRINT2_ACCEPTANCE.md).
Full seven-feature/context preservation and PostgreSQL concurrency are not certified.

Recent queries are limited to one session/mode and 24 hours of observation time,
with cursor pages at most 200 records. The explicit pruning command deletes at
most 1000 rows per sample/window/status table older than 24 hours by receipt time;
session manifests remain. These are the implemented bounds. The larger global
row/byte admission, automatic cleanup and database throughput budgets below
remain future proposals, not capabilities of this minimal backend.

## Windows Companion SQLite schema v1 (source audit 2026-10-05)

The companion has its own private `%LOCALAPPDATA%\NetSentinel\state\companion.sqlite3`.
It does not share the lab database or Django models. The following are the actual
`companion/store.py` table names, correcting earlier logical-only entity names.
`PRAGMA user_version=1`; unknown versions fail closed.

| Table | Stored fields and purpose |
| --- | --- |
| `apps` | Executable hash id, canonical path, name, protection flag, last-seen timestamp |
| `usage` | `(app,day,mode)` key and observed upload/download IP byte totals; unassigned preserved |
| `policies` | App key, daily/monthly quotas, warning percent, direction, auto-block flag, override deadline, manual intent |
| `events` | Time, app, category, code, bounded message, provenance, unique deduplication marker |
| `flows` | App, observation time, protocol, remote IP/port, upload/download bytes, provenance |
| `destinations` | `(app,remote,mode)` key and last observation time |
| `settings` | Key and JSON-encoded local preference value |

Time values are UTC epoch seconds; daily usage keys are UTC date strings.
Retention is 90 days of daily usage, up to 10,000 flow rows/7 days, 2,000 audit
rows/90 days, and 5,000 destinations/30 days. Discovery is capped at 512 apps.
No packet payload or URL field exists. The database has no per-process packet
counter column; byte attribution remains the approximate collector's evidence.
Retention does not certify a fixed SQLite file-size bound.

PostgreSQL is the planned system of record for a simple local backend, introduced only in an authorized Sprint 2 after Sprint 1 passes. This is a logical contract, not migrations. Use UUID identifiers, timezone-aware UTC, foreign keys, explicit checks and versioned migrations. One database suffices; no time-series extension, per-mode database, job queue or event-sourcing system.

## Staged minimum entities

| Stage / entity | Required data |
| --- | --- |
| Sprint 2: Django user, if needed | Built-in local operator identity/password/session handling; no custom role hierarchy. |
| Sprint 2: Sensor | Local source identity, restricted upload credential hash/reference, allowed modes, agent version and last seen. |
| Sprint 2: Interface | Sensor, stable OS/capture identity, alias, selected address/capability context, interface state and observation time. Sensitive metadata stays local. |
| Sprint 2: SourceSession | Locally generated UUID, sensor, immutable mode, run ID, start/end/status, observation profile and capability/config/schema versions. Physical interface required for LIVE capture only; recovery opens a new session in the same run. |
| Sprint 2: InterfaceSample | Session/interface, sequence, sample start/end, actual OS totals/deltas/rates, elapsed time, measurement source and validity/reset/missing flags. |
| Sprint 2: FlowWindow | Session, canonical protocol/endpoints/nullable ports, ten-second interval, first/last/finalized/processed times, directional IP packet/byte counts, TCP/SYN and UDP statistics, observed length range and partial/loss flags. A flow segment is not a full connection. |
| Sprint 2: CaptureStatus / MonitoringGap | Run/session, RUNNING/INTERFACE_LOST/RECOVERING/STOPPED, observed loss/recovery times, reason, attempts, last seen and validity. One small status table may represent both events and gaps. |
| Sprint 2: IngestionReceipt | Sensor/session/stream/batch ID, digest, sequence, accepted counts and commit time; never raw request bodies. |
| Sprint 4: FeatureWindow | Session, host/interface profile, interval, host-v1 schema, nullable vector, sufficient statistics and quality flags. Preserve Sprint 1's existing embedded features as bounded window metadata until separate querying is needed. |
| Sprint 4: ModelVersion | Trusted local artifact path/reference and digest, feature/profile/preprocessing/library versions, training/split manifest, seed, threshold and evaluation metadata. No artifact blob or arbitrary upload. |
| Sprint 4: AnalysisResult | Feature reference, actual loaded model/version, nullable score/threshold/Normal-or-Anomalous label, availability reason and observed/finalized/processed/received times. Missing ML is null, never Normal or zero score. |
| Sprint 5: Explanation / LabRun | Bounded versioned explanation evidence on analysis/window records; run mode, scenario/input digest, seed, virtual-clock settings, source sessions and status. Rule-only evidence permits unavailable ML. Avoid separate tables where bounded JSON is sufficient. |

Local model selection/load is manual and versioned; retain the previous compatible artifact for rollback. No distributed model-assignment orchestration is required. Minimal sanitized security/activation/cleanup events can use a bounded operational log rather than an enterprise audit product.

## Integrity and provenance

All metadata retains immutable LIVE / SIMULATION / REPLAY, source/session/run identity and observation profile. Validate cross-table agreement in transactional services and appropriate composite keys/constraints; a simple SQL CHECK cannot check arbitrary related rows. Never attach synthetic or replay evidence to LIVE. Gaps carry no fabricated traffic samples. Keep original event time distinct from ingestion time.

Unique ingestion key: (sensor_id, session_id, stream, batch_id); different content under the same key is a conflict. Samples are unique by session/sequence; flows by session/canonical tuple/window start; feature windows by session/profile/window/schema; analysis by stable feature/model/rule-version identity. Validate finite numeric values, nonnegative counts and start < end. Retried records cannot duplicate totals or findings.

Keep remote IPs/ports as flow endpoints, not permanent Device records. Local host identity derives from the sensor plus validated interface addresses, not a public IP or gateway MAC. Null ports, unknown attribution and unsupported features remain explicit. Retain sufficient statistics and required version/reference context with explanation evidence until its own expiry; never cascade into an inconsistent surviving finding.

## Queries and bounded retention

Initial indexes: flows/features (session_id, window_start), samples (session_id, sample_end), status (run_id, observed_at), analysis (session_id, observed_at), and unique receipts. Use bounded time ranges and cursor pagination. No JSON index per feature or materialized summary system without measurement.

Proposed initial retention: routine samples, flows, health/status, features and analysis/explanations for 24 hours. Keep source/lab/model manifests while retained dependent records require them; keep active and one rollback artifact with evaluation manifests. Minimal operational/security logs expire after 90 days with a separate provisional 50 MiB cap and visible pressure handling. Reviewed research exports need explicit consent, private location, bounded size and expiry; telemetry cleanup must not silently destroy an approved training experiment. Replay inputs are removed after processing by default. No routine packet/payload storage.

Preserve the proposed combined telemetry budget of 1,000,000 rows or 2 GiB table-plus-index storage, whichever is reached first; start cleanup at 80%. Include samples, flows, features, status/gaps, findings, receipts and dependent manifests in measured budgets. Check at startup and at least every minute, with bounded oldest-first cleanup and per-batch admission. Use a documented local management command/native schedule, no Celery/Redis. Require at least 1 GiB free headroom; expose storage pressure and reject detailed ingestion explicitly if cleanup cannot recover. Keep a bounded status path while storage permits.

Receipt retention is at least 24 hours, exceeding the maximum 15-minute transport retry age; at admission failure, reject uploads rather than evicting receipts early and risking duplication. Expired uploads cannot be reinterpreted as new data. Bounds are proposed and require actual PostgreSQL measurements. Row deletion can reuse database space without reducing allocated disk size: measure cleanup, VACUUM, indexes/WAL and backup expiry/restoration.

At 100 nonempty keys per ten-second window, flow rows alone reach 864,000/day; 10,000 keys would reach 86.4 million/day. The sensor cap is not a database throughput promise. Benchmark 100,000-row reads and near-budget writes/cleanup. Prefer shorter retained detail with explicit coverage over an unbounded history. Never add overlapping OS-counter and packet-byte totals together.

## Historical schema — OUT OF SCOPE

The former proposed NetworkScope/site hierarchy, Device/DeviceAddress/DeviceObservation inventory, RiskAssessment, Incident/IncidentEvidence/IncidentEvent, Alert, ReportJob, generic PolicyVersion and enterprise audit/role/model-assignment workflow are removed from active delivery. They were plans, not existing migrations or data to delete. Dedicated hourly summary/report infrastructure is not required. Preserve historical reasoning in ARCHITECTURE_REVIEW.md; do not scaffold these entities.
