# API and event plan

Proposed /api/v1 routes, staged by sprint; no backend is implemented by this cleanup. Use JSON, UUIDs, UTC ISO-8601 timestamps, immutable mode/session/run/profile identifiers and finite numeric values. Bounded cursor pages default to 50, maximum 200; detailed queries cover at most the retained 24 hours initially. Errors include code, message, field details and request_id, without stack traces: 400 validation, 401 unauthenticated, 403 forbidden, 404 unavailable, 409 conflict, 413 oversized, 429 throttled, 503 temporary unavailability.

## Minimal access and staged routes

Use a local operator identity with server-side authorization and a separate revocable ingestion credential scoped to source and allowed modes. Django session authentication with CSRF protection is the starting proposal; decide/document exact setup in Sprint 2. No administrator/analyst/viewer role product or mandatory JWT/ticket infrastructure. Default services bind to loopback; UI buttons never substitute for authorization.

| Sprint | Routes | Purpose / authority |
| --- | --- | --- |
| 2 | POST /auth/login, /auth/logout; GET /auth/me, if needed | Built-in local operator login/session, CSRF and throttling; no user-management screens. |
| 2 | GET /sensors, /interfaces, /interfaces/{id}, /health | Authorized operator reads genuine source/interface state, capture capability and last observed time. Provision one sensor credential locally via a management command. |
| 2 | POST /sensor/sessions; POST /sensor/sessions/{id}/close | Source credential registers its local UUID/mode/profile and completion; never initiates capture. |
| 2 | POST /ingest/batches; POST /sensor/heartbeat | Scoped source telemetry, flow and status ingestion; heartbeat is a future transport record, not an existing Sprint 1 external consumer. |
| 2 | GET /interface-samples, /flows, /capture-status, /monitoring-gaps | Real samples, bounded flow summaries, state events and missing coverage, filtered by mode/session and run. |
| 3 | GET /dashboard/summary, /analytics/traffic | Small derived views over accepted telemetry for rates, packets, TCP/UDP, active window flow keys and recent traffic charts. |
| 4 | GET /features, /models, /detections | Actual model manifest, complete-window Normal / Anomalous results, score/threshold/version and unavailable states. Trusted training/save/load/selection remain local CLI operations. |
| 5 | GET /explanations, /labs/scenarios, /labs/runs/{id}; POST /sensor/lab-status | Computed feature/rule evidence and labelled run progress/results. Local CLI launches isolated simulation or supported replay; scoped lab credentials upload actual results. |

Require mode for telemetry/analysis reads; lab reads also require run ID. Never combine all modes implicitly. Validate every referenced source/session/window. Return units, measurement_source, observation_profile, capture_capability, schema/quality, observed and received time, resolution and coverage. Distinguish idle, missing, partial, stale and delayed. No physical interface is invented for a lab source. Normal is reserved for a scored compatible complete window.

## Ingestion contract

The versioned envelope contains schema_version, stream (telemetry or later analysis), batch_id, sensor_id, registered local session_id, run_id where relevant, mode, observation_profile, sent_at, sequence and agent_version. Telemetry arrays contain genuine interface samples, flow/window metadata and capture status/gaps. Preserve existing Sprint 1 host-v1, quality/capability context, directional counts and timestamps through an explicit adapter; do not rewrite the capture contract to match ORM fields.

Analysis carries durably accepted feature/window references, actual feature/preprocessing/model/rule versions, nullable ML output and computed explanation evidence. Reject incompatible analysis separately without losing valid samples/flows. Local source-session creation never depends on backend availability; registration is required only before upload. Recovery creates new sessions linked by run ID, never windows spanning a gap. Lab credentials/modes cannot rebind an existing LIVE session.

Provisional limits: 500 records or 1 MiB uncompressed per batch, whichever first. Atomic acceptance returns accepted counts, stream/batch ID, committed_at and duplicate status only after commit. Unique (sensor, session, stream, batch_id) plus digest makes identical retry safe and changed-payload reuse a 409. Stable record IDs prevent duplicates across batches. Keep receipts at least 24 hours; transport retry age is at most 15 minutes. Original REPLAY time may be older; newly processed batches still obey transport limits.

Use bounded retries/backoff/jitter for 429/503/network failure and respect Retry-After. Schema/version/auth failures are explicit and cannot loop indefinitely. Count discarded spool records; sequence gaps expose uncertainty. LIVE observations over a proposed 30 seconds old are delayed, not current merely because received now. Invalid clocks disable real-time interpretation. No analysis result triggers automatic blocking or external notifications.

## Dashboard updates: REST first

Sprint 3 starts with approximately one-second polling of bounded latest telemetry/status views while active. Show actual observation time and measured latency; polling never synthesizes one-second data. Cancel/ignore responses from old mode/run/query keys, avoid overlapping requests, back off on errors and refresh authoritative state after reconnection.

Django Channels/WebSockets are conditional only if measured polling cannot meet the latency/resource target. They are not Sprint 2 scaffolding prerequisites. If adopted, authorize subscriptions server-side, validate Origin and expiry/revocation, publish minimal hints after commit, and refresh REST after missed events/reconnect. Keep HTTP ingestion and sockets in one ASGI process for a local in-memory layer; external sensor processes post via HTTP. No durable/exactly-once push guarantee. A shared layer/Redis would require a separately justified necessity and explicit decision; no cloud/multiworker deployment requirement.

## Historical API surface — OUT OF SCOPE

Remove active routes for /users role administration, /devices inventory, /incidents and transitions/notes, /alerts, /topology, /reports and report jobs, enterprise /audit-events or generic /settings consoles, browser capture/stop commands and sensor command polling, UI-launched/cancelled background jobs, and remote model activation/assignment orchestration. The previous JWT rotation/single-use WebSocket-ticket design is a superseded deployment proposal, not mandatory setup. Minimal access checks, local capture permission, trusted model handling, provenance and retention remain required; see SECURITY_RULES.md.
