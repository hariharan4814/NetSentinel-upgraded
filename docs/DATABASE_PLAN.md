# Database plan

PostgreSQL is the planned system of record. This is a logical schema, not migrations. Use UUID identifiers, timezone-aware UTC timestamps, foreign keys, explicit enums/checks, and migrations from the first implementation. API time ranges are half-open [start, end).

Implement tables incrementally with the owning sprint. One PostgreSQL instance/database is sufficient; no time-series extension, per-mode database, general job queue or event-sourcing platform is required. Mode/session scope uses indexed relational fields and constraints. Keep web ORM models separate from sensor contracts.

## Entities

| Entity | Important fields and relationships |
| --- | --- |
| User/role | Django user identity, active state, role membership and auth/session version for revocation; framework refresh-blacklist records where used; no custom password storage |
| Sensor | Name, enrollment state, credential hash/reference, allowed modes, last heartbeat, agent version |
| NetworkScope | Authorized network/site identifier, scope policy, owner; groups comparable observations |
| Interface | Sensor FK, stable OS identifier where available, name, type, addresses, capability evidence and last seen |
| SourceSession | Locally generated UUID, sensor/scope FKs, interface FK required only for live capture, immutable mode, start/end/status, observation profile/capability/config versions; lab/replay has a logical source with no invented physical interface |
| Device | Scope, mode, identity namespace, display name, confidence, first/last seen, operator annotation |
| DeviceAddress | Device FK, IP/MAC where observable, validity interval, source session and confidence |
| DeviceObservation | Device/session FKs, observed time, method, evidence summary; missing identity allowed without invented device |
| InterfaceSample | Session/interface, sample start/end/sequence, OS counter deltas/rates, measurement source, reset/missing/quality flags; actual one-second samples, not inferred from ML windows |
| FlowWindow | Session FK, canonical key and endpoint tuples, start/end, protocol, optional attributed device FKs, directional IP packet/byte counts, TCP/SYN and UDP sufficient counts, quality/drop flags; a time segment, not a whole connection |
| FeatureWindow | Session, subject_kind (host/interface/device), stable subject_key, optional device FK, interval/duration, feature schema, observation profile, numeric vector and sufficient statistics/quality flags; host is MVP |
| ModelVersion | Trusted artifact reference/digest, observation profile/schema/preprocessing/library versions, allowed mode, training manifest, seed/split/cutoffs, metrics and thresholds, status/approval; no artifact blob |
| ModelAssignment | Sensor/scope/mode/profile, desired model, acknowledged actual model, status/applied interval and actor; one applied assignment per (sensor, scope, mode, profile), change at window boundary |
| Detection | FeatureWindow FK, nullable model FK/score/threshold/anomaly flag for rule-only analysis, rule/version evidence, observed/finalized/processed/received times, classification and delayed state |
| RiskAssessment | Subject kind/key (host/interface/device/incident), policy version, component scores/availability, resulting priority, evidence and calculation time |
| Incident | Mode/scope/session/run and subject, correlation key, peer/rule, first/last observed, severity, classification, lifecycle, disposition, assignee, summary, optimistic revision and evidence snapshot |
| IncidentEvidence | Incident and detection FKs; provenance must agree; links permit multiple findings per incident |
| IncidentEvent | Incident FK, actor, prior/new status or note, reason, created time |
| Alert | Incident/user FKs, deduplication key, delivery/read state and timestamps |
| HealthSample | Sensor/interface/session, observed time, heartbeat lag, loss counters, optional approved probe latency and availability |
| HourlySummary | Mode/scope/profile/source, hour start/end, separately aggregated OS and packet metrics, resolution/coverage and calculation version; unique source-hour key prevents double counting |
| LabRun | Mode, scenario/input digest, seed, virtual-clock settings, source session, status, creator and error |
| ReportJob | Advanced only: requestor, mode/scope/time filters, status, expiring output and error. MVP uses a bounded direct CSV export with audit |
| AuditEvent | Actor kind/ID, action, object reference, result, request ID, timestamp, sanitized changes |
| PolicyVersion | Type, validated settings, version, creator and effective time; secrets stored separately |
| IngestionReceipt | Sensor/session/stream/batch ID, payload digest, sequence, accepted counts, committed time; no raw request payload |

Raw packet storage is excluded. Unknown ports/protocol-specific fields are nullable; do not force TCP concepts onto ICMP. JSON fields support bounded versioned evidence/features, not arbitrary payload dumps or replacement of indexed relational fields.

## Integrity and identity

Unique ingestion key: (sensor_id, session_id, stream, batch_id). Reuse with a different digest is a conflict. Flow uniqueness includes session, canonical protocol-specific tuple, and window start. Sample uniqueness includes session and sample sequence. Feature uniqueness includes session, subject kind/key, window start, and schema version. Findings have stable IDs and unique analysis-version references to prevent duplicate incidents even if retried under another batch ID. Validate nonnegative counts and start < end. At capacity discard new flow keys with quality flags rather than emitting colliding segments.

LIVE identity namespace is the authorized network scope; SIMULATION and REPLAY namespaces include run ID so reruns cannot silently merge devices. IP addresses alone are observations, not permanent identities. MAC randomization, NAT, IPv6 privacy addresses, and absent link-layer metadata make automatic merging uncertain; retain confidence and auditable manual corrections.

Keep ordinary remote endpoints in flow tuples until evidence supports a Device record; do not create a permanent LAN device per destination IP. Store attribution_method, confidence and validity time when assigning a flow to a device. The local host is identified by sensor enrollment, not public IP. Router next-hop MACs and post-NAT traffic cannot establish remote-device identity.

Enforce session/mode agreement for related records in domain validation and appropriate database constraints. An incident cannot link evidence from another mode. Deleting a user must not erase historical incident/audit attribution. Telemetry expiry must not cascade-delete incidents; preserve minimal evidence snapshots with explicit retention expiry.

Cross-table provenance is not enforceable by a simple SQL CHECK alone: use composite constraints/keys where appropriate and transactional service validation with integration tests. Avoid unrestricted polymorphic IDs for integrity-critical evidence. Expired raw feature/detection links become nullable or are pruned after copying minimal evidence; immutable incident snapshots include schema/model/rule versions and required feature values. A rule-only finding has an unavailable ML value, never a synthetic zero score.

## Query and retention plan

Initial B-tree indexes: flows/features (session_id, window_start), samples (session_id, sample_end), observations (device_id, observed_at), incident (mode, status, last_observed), detection (session_id, observed_at), audit (created_at), and unique receipts. Use table-specific timestamp names consistently in migrations/API mapping. Avoid redundant indexes and an index per JSON feature. Partitioning/materialized summaries require measured need; batch inserts and bounded range queries come first.

Initial age limits: samples, flows, routine health, feature windows and unlinked detections/risk history 24 hours; minimal hourly summaries/device observations 7 days; incidents and their copied evidence/events/risk history, alerts and audit 90 days. Device/address records with no retained observations or investigation references expire after 7 days of inactivity; local enrollment identity remains. Session/lab/model manifests survive only as long as retained data/evidence needs them. Approved research feature exports have explicit separate consent, location, size and expiry (never implied indefinite retention). Keep active and one rollback artifact plus their evaluation manifests. Advanced generated reports expire within 7 days; replay inputs are deleted after processing by default.

Age alone is not a storage bound. Proposed combined telemetry limits are 1,000,000 rows or 2 GiB measured table-plus-index storage, whichever is reached first, with cleanup starting at 80% to reserve room for bursts. Include samples, flows, features, routine health, unlinked findings/risk, summaries and receipts in this budget. Perform startup and at least minute-based budget checks plus bounded oldest-first cleanup from Sprint 2, using one documented native scheduled/management mechanism and per-batch admission limits. Publish storage-pressure/gap status; pause detailed telemetry ingestion with an explicit retryable response if cleanup cannot restore the limit. Preserve a bounded status/control path while storage remains available; keep incident/audit growth separately monitored rather than deleting investigation records to hide pressure. Require at least 1 GiB free disk headroom and fail visibly if unavailable. Exact thresholds are provisional and must be benchmarked; row deletion may reuse existing DB space without lowering the allocated-size reading.

Capacity example: 100 nonempty flow keys each 10-second window produce 864,000 rows/day; 10,000 produce 86.4 million/day. Therefore the active-key cap is not sustainable database throughput and a 100,000-row query test cannot validate seven-day retention at that load. Measure row/index size, write rate, cleanup throughput, Windows service baseline and p95 reads. Use shorter retention or coarser summaries with explicit resolution/coverage rather than storing every packet. Hourly summaries sum nonoverlapping source intervals once; never add overlapping OS-counter and packet-byte series or silently treat approximate distinct-peer counts as exact.

Cleanup covers artifact files, spools and database records. Receipts live at least 24 hours, longer than the 15-minute spool and maximum permitted retry age; expired old uploads are rejected, not reinterpreted as new events. Preserve bounded summaries before expiry where supported, and expose loss if unavailable. Record VACUUM/disk-reuse behaviour; ordinary row deletion is not an immediate guarantee of operating-system disk reclamation. Restricted backups have separate expiry and tested restore. Audit is append-only through the application, not tamper-proof against a database administrator.
