# API and event plan

All routes are proposed under /api/v1, implemented only with their owning sprint. Use JSON, UUIDs, UTC ISO-8601 times, explicit mode/session/profile identifiers, bounded page sizes (default 50, maximum 200), and stable cursor pagination for time series. Errors have code, message, field details and request_id without stack traces. Return 400 validation, 401 unauthenticated, 403 forbidden, 404 unavailable resource, 409 state/idempotency conflict, 413 oversized body, 429 throttled, and 503 for temporary storage/service unavailability with retry guidance.

## Roles and resources

Administrator manages enrollment, capture policy, users and model approval/assignment. Analyst reads operational telemetry, reviews models, runs approved isolated labs, manages incidents and exports reports. Viewer reads dashboard/health/incident summaries and own alerts only; detailed flows, inventories, lab inputs, configuration and exports require analyst/admin. Sensors have separate machine credentials bound to allowed modes/scopes; they cannot call human routes. Validate all body/reference IDs. Backend enrollment is required only for uploads, not locally authorized standalone collection.

| Endpoints | Purpose and permission |
| --- | --- |
| POST /auth/token, /auth/refresh, /auth/logout; GET /auth/me | Human login/rotation/revocation and current permissions; login throttled |
| GET/POST /users; PATCH /users/{id} | Administrator user/role management |
| GET/POST /sensors; POST /sensors/{id}/rotate-credential, /revoke | Read sensor status; administrator enrollment/control |
| GET /interfaces; GET /interfaces/{id} | Observable capabilities, addresses and status |
| POST /sensor/sessions; POST /sensor/sessions/{id}/close; GET /capture-sessions/{id} | MVP: sensor registers its local session UUID/capabilities and completion; authorized humans read status. No backend-generated capture required |
| POST /capture-sessions; POST /capture-sessions/{id}/stop; GET /sensor/commands; POST /sensor/commands/{id}/ack | Advanced: administrator request and enrolled local runner polling/ack; 202 is queued, not running. MVP has local start/stop only |
| POST /ingest/batches; POST /sensor/heartbeat | Scoped sensor telemetry and health |
| GET /devices, /devices/{id}, /devices/{id}/history | Mode-filtered inventory and observations |
| GET /interface-samples, /flows, /features, /detections, /health | Scoped read models with timestamps, measurement sources and capabilities; viewer receives health summaries only |
| GET /models; POST /models/register; POST /models/{id}/activate, /rollback; GET /sensor/config; POST /sensor/model-status | Administrator registers trusted local manifest/desired assignment; sensor reads scoped validated configuration and acknowledges actual applied version/error; artifacts transferred locally, no arbitrary upload |
| GET /incidents, /incidents/{id}; POST /incidents/{id}/transitions, /notes | Read evidence; analyst/admin audited workflow changes |
| GET /alerts; POST /alerts/{id}/read | User's in-app alerts and read state |
| GET /dashboard/summary, /analytics/traffic | MVP real sample/short-history read models; timestamp/source/coverage mandatory |
| GET /topology | Advanced observed communication graph, not physical wiring |
| GET /labs/scenarios, /labs/runs/{id}; POST /sensor/lab-status | MVP Lab view/status; a locally authorized CLI with a lab-scoped credential launches isolated scenarios and uploads actual results |
| POST /labs/simulation-runs; POST /labs/runs/{id}/cancel; POST /labs/replay-runs | Advanced UI launch/replay: implement only with an explicit local runner/job lifecycle and quotas; do not execute in requests |
| GET /reports/traffic.csv | MVP analyst/admin bounded export (maximum 10,000 rows / 24 hours); fail with request-to-narrow filters if over cap, never silent truncation |
| POST /reports; GET /reports/{id}; GET /reports/{id}/download | Advanced asynchronous exports: defined worker, expiry and download reauthorization required |
| GET /audit-events; GET/PATCH /settings | Administrator audits/settings; redact secrets |
| POST /realtime/tickets | Authenticated user obtains short-lived single-use WebSocket ticket |

Mode is required for telemetry/analytics/lab reads; never silently aggregate all modes. Filters include from/to, sensor, device, classification, severity, and lifecycle as relevant. Impose query range and export limits; return resolution, coverage, last_observed_at, and partial/stale indicators.

Default detailed query horizon is the retained 24 hours, maximum 24 hours initially. Lab reads also select run ID. Include measurement_source, observation_profile, capture_capability, attribution confidence, ML availability, latest received time and collection gaps. Freshness uses observed time; delayed backlog is historical even when newly ingested. JWT/cookie/CSRF and socket revocation rules are in SECURITY_RULES.md.

## Ingestion contract

A batch envelope contains schema_version, stream (telemetry or analysis), batch_id, sensor_id, registered local session_id, mode, observation_profile, sent_at, sequence and agent_version. Telemetry contains bounded arrays of real interface samples, observations, flow segments and feature windows/quality flags. Analysis contains feature references, actual model/rule/schema versions, scores/evidence and processing timestamps. Both retain observed intervals; finalized_at and processed_at are distinct from received_at for LIVE as well as REPLAY.

Backend registration binds local session UUID and immutable mode/profile to the credential scope; reject attempted rebinding. Simulation/replay sources have no required physical interface. Separate live and lab credential profiles prevent a run selector from promoting synthetic data. Feature windows may summarize many flow batches; mark coverage only after their contributing windows are finalized. Analysis references already accepted features in the same session; the sender waits for their receipt before sending analysis. Incompatible analysis is rejected without discarding valid telemetry, and is surfaced as ML/analysis unavailable.

Provisional limits: 500 records or 1 MiB uncompressed per batch, whichever occurs first. A single oversized evidence record fails; use bounded summaries, not unrestricted arrays. Atomic acceptance per stream/batch returns batch_id, stream, accepted counts, committed_at and duplicate status. Unique key is (sensor, session, stream, batch_id); identical retry returns the receipt and different digest returns 409. Record-level stable IDs also prevent duplicates across batch IDs. Never acknowledge before transaction commit. Retain receipts at least 24 hours; maximum transport retry age is 15 minutes. Replay's original timestamp may be old, but its newly processed batch obeys the same transport-age bound.

Retry transient 429/503/connection failures with backoff/jitter and Retry-After where provided. Invalid schema/model batches enter bounded quarantine, not an infinite retry loop. A sequence gap marks coverage uncertainty. LIVE observations over 30 seconds old are marked delayed; store them within allowed retention but suppress real-time alert notifications initially. Delay is evaluated against session clock quality; invalid clocks disable real-time interpretation. SIMULATION and REPLAY use their event clock for correlation while permanently labelled by mode.

Advanced commands require IDs, expiry, scope, fixed operation enum and idempotent acknowledgment. The local runner rejects missing privilege or absent operator authorization. No arbitrary shell command is accepted. A local operator can always stop collection; backend configuration cannot grant Windows privileges or guarantee offline shutdown.

## WebSocket contract

Proposed path: /ws/v1/events. Obtain a 30-second single-use ticket over the authenticated API and present it as a ticket query parameter for the browser handshake. This is the sole URL-token exception: redact query strings in ASGI/proxy logs and use HTTPS/WSS outside the explicit loopback development exception. Never put access/refresh JWTs in URLs. Bind the ticket/socket to user, scope, mode, run where relevant, and access-session expiry. Consume atomically; validate Origin. Poll authorization state at least every 5 seconds and close on revocation/expiry, rather than assuming SimpleJWT closes sockets automatically.

Envelope fields: event_id, event_type, schema_version, emitted_at, mode, scope_id, session_id/run_id when relevant, object_id and minimal payload. Types: telemetry.updated, sensor.status_changed, detection.created, incident.updated, alert.created, lab.status_changed. No packet payloads or unrestricted inventories. Keep HTTP ingestion and socket consumers in one ASGI process; external sensor/CLI processes never publish to an in-memory channel layer directly.

Events can be missed, duplicated or delayed. Deduplicate by event_id and invalidate/refetch mode/session-scoped TanStack Query snapshots. UUIDs do not establish a gap-free event sequence: reconnect/mode changes always refresh REST, and active pages reconcile at least every 15 seconds even with a connected socket. If the socket fails, visibly use 5-second REST polling. There is no exactly-once/durable push replay guarantee. Limit telemetry notifications to at most one per second per session from accepted one-second samples; ten-second flow/model updates follow their own actual finalization. Do not create empty events as fabricated activity.

## Incident transitions

Allowed analyst/admin transitions: OPEN → ACKNOWLEDGED → INVESTIGATING → RESOLVED → CLOSED; RESOLVED/CLOSED → INVESTIGATING is a reason-required reopening. Resolution requires disposition and note. Severity and classification are separate from lifecycle. Use a version field or equivalent optimistic concurrency check; stale updates return 409. Append actor/time/reason to the incident event and audit log in the same transaction.
