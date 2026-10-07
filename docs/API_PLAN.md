# API and event plan

## Implemented SIMULATION AI Lab API — 2026-10-05

The versioned request/result shapes are in [AI_LAB_CONTRACT.md](AI_LAB_CONTRACT.md).
Django stores bounded jobs in `experiments`; fitting occurs only in the independent
`python -m lab.worker` process. This interface cannot run shell commands, choose
paths, capture packets, publish LIVE models, or change Windows security controls.

| Method/path under `/api/v1/lab/` | Credential | Behaviour |
| --- | --- | --- |
| GET `jobs/`, `jobs/<uuid>/` | `NETSENTINEL_READ_TOKEN` | Latest 20 summaries; detail includes a completed result |
| POST `jobs/` | `NETSENTINEL_LAB_TOKEN` | Validated `{config}`; 201 or 429 if four jobs wait |
| POST `jobs/<uuid>/cancel/` | `NETSENTINEL_LAB_TOKEN` | Empty object; queued cancellation or running cancellation request |
| POST `worker/claim/` | `NETSENTINEL_LAB_WORKER_TOKEN` | One running lease maximum; raw lease sent only to worker |
| POST `worker/<uuid>/heartbeat/` | Worker token + lease | Renew 30-second lease; actual stage/counts and cancellation flag |
| POST `worker/<uuid>/finish/` | Worker token + lease | Bounded validated SIMULATION result or terminal failure/cancellation |

Inputs reject unsupported keys, query parameters, duplicate JSON keys, non-finite
numbers and invalid UUID routes. Only authenticated worker finish has a 4 MiB
body allowance; other requests retain 64 KiB. Lease hashes, tokens and artifact
paths never appear in job serializers. Arbitrary failure messages are discarded
in favour of a fixed message. Expired RUNNING jobs become FAILED/interrupted on
the next job operation. Completed cancellation is idempotent; finish requires
the active lease and is not replayable. Network failure after a finish response
may therefore be ambiguous to the worker; read the retained job before retrying.

The browser uses authenticated same-origin `/api/lab/jobs` relays with exact
Origin, session and CSRF checks for mutations. It has no worker credential.
Explicit `config.lab_settings` exposes only lab routes with a separate SQLite
database; normal `config.settings` preserves PostgreSQL and research APIs.
No automatic database fallback exists. Tests cover temporary SQLite concurrency
and fresh-process persistence; PostgreSQL concurrency remains a separate gate.

## Public browser utility & external measurements — 2026-10-02

Public `GET /connection-check.json?check=<random-id>` serves fixed
`{"service":"netsentinel-connectivity","version":1}`. No user content is
stored or echoed. Browser requests use no-store, omit credentials, reject
redirects and time out after 3 seconds. A run has exactly eight attempts unless
cancelled. The request URL is fixed; this is not a proxy or a speed-test endpoint.
Hosting sets no-store for this asset; real HTTP times include server/browser
overhead and are scoped only to this website.

Measured speed and IP lookup contracts:
- **Cloudflare Speed Engine**: User-initiated via `@cloudflare/speedtest` (pinned 1.14.1). Runs against public Cloudflare endpoints (`speed.cloudflare.com`). Bounded payloads (nominal 15.5 MB budget, max 62 MB cap). Measures download, upload, latency, and jitter. Real application-layer throughput, never raw wire estimates. Consent required; cancellable at any phase.
- **Visitor-side IP & Provider Lookup**: Uses direct `https://ipwho.is/` fetch from the visitor's browser. No server proxy. Default-redacts IP and location; requires explicit user toggle.
- See [PUBLIC_MEASUREMENTS.md](PUBLIC_MEASUREMENTS.md) for endpoint details and failure modes.

The public static build has no `/api/backend/*` or `/local`. The local
gateway and sensor API documented below remain available only in the local
Next/Django stack. Public history and reports are computed in the browser.

## Upgraded local research authentication (2026-10)

The local Django and Next.js relay are no longer unauthenticated:
- **Django REST Backend** (`http://127.0.0.1:8001`):
  Requires `Authorization: Bearer <token>` on all ingestion and query endpoints:
  - `NETSENTINEL_READ_TOKEN`: Required for GET on permitted read endpoints.
  - `NETSENTINEL_INGEST_TOKEN`: Required for POST on monitoring-sessions, telemetry, windows and capture-status.
  - `NETSENTINEL_MODEL_TOKEN`: Required for model-versions and anomaly-results publication from `ml/`.
  - Unauthenticated requests receive HTTP 401 (`{"error":"authentication_required"}`).
- **Next.js Gateway Relay** (`http://127.0.0.1:3000`):
  - Operator sign-in at `POST /api/local-auth` sets an HttpOnly, SameSite=Strict session cookie.
  - Requires matching CSRF token in `x-csrf-token` header for state-changing operations.
  - Rate limiting: max 5 failed attempts per minute per loopback client.
  - See [LOCAL_AUTH.md](LOCAL_AUTH.md) for full configuration and session lifecycle.

## Windows Companion Local API (`http://127.0.0.1:8765`)

The installed Windows companion operates an authenticated loopback server:
- **Binding**: `127.0.0.1:8765` only; non-loopback connections rejected.
- **Authentication**: `Authorization: Bearer <token>` where `<token>` is read from `%LOCALAPPDATA%\NetSentinel\state\access.token` (minimum 32 bytes, constant-time comparison).
- **Host & Origin Security**: Validates `Host: 127.0.0.1:8765`. Rejects foreign origins; POST requires exact same-origin (`http://127.0.0.1:8765`).

### Endpoints
- `GET /api/snapshot`: Returns full JSON snapshot containing:
  - `apps`: Discovered applications, SHA-256 executable IDs, display names, today/month usage bytes, active quotas, should_block state.
  - `unassigned`: Total unassigned observed bytes and packet count.
  - `capture`: Capture status (interface, state, packets, drops, socket snapshot completeness).
  - `enforcement`: Boolean switch state.
  - `controls`: Per-application firewall control state.
  - `security`: Microsoft Defender and Windows Firewall profile status.
  - `scan`: Defender scan status.
- `POST /api/action`: Executes a bounded control action:
  - `policy`: Update app quota thresholds, modes (observe/enforce), and overrides.
  - `control`: App block/unblock intent (enforcement must be enabled).
  - `enforcement`: Toggle system-wide quota enforcement (disabling triggers automatic rule cleanup).
  - `capture-start` / `capture-stop`: Explicit interface selection and consent for Npcap capture.
  - `security`: Query Defender and firewall status.
  - `scan` / `scan-status`: Trigger Quick or Full Defender scan (requires explicit user consent).
  - `cleanup`: Remove all NetSentinel-owned firewall rules.
  - `report`: Generate semantic private PDF report with optional section selection and privacy redaction.

## Privileged Windows Security Broker API (`http://127.0.0.1:8766`)

The privileged broker runs in an elevated shell and exposes a minimal, hardened attack surface:
- **Binding**: `127.0.0.1:8766` only.
- **Authentication**: `Authorization: Bearer <token>` where `<token>` is read from `%LOCALAPPDATA%\NetSentinel\state\broker.token` (distinct from access.token).
- **Origin Rejection**: Completely forbids browser `Origin` headers (returns HTTP 403 if present) to block browser-based drive-by attacks.
- **Fixed Operations**:
  - `heartbeat`: Validates broker responsiveness and updates the 30-second lease.
  - `rules`: Queries currently active NetSentinel-owned firewall rules via NetSecurity cmdlets.
  - `block`: Adds inbound and outbound block rules for a resolved executable path (fails closed if path is non-canonical or a system critical executable).
  - `unblock`: Removes owned rules for the application.
  - `cleanup`: Removes ALL NetSentinel-owned firewall rules (`RuleGroup: NetSentinel-Companion`).
  - `scan`: Initiates `Start-MpScan` via Defender cmdlets with explicit scan type.
  - `scan-status`: Queries Defender scan job progress.
- **Protection**: Rejects arbitrary commands, executable paths, or script text from caller. Paths are verified against known executable IDs in trusted companion storage.


Sprint 3 is **PASS for the agreed local dashboard integration scope** with the
GET contracts below unchanged. [Final evidence](SPRINT3_ACCEPTANCE.md) records
operator PostgreSQL/browser readback and outage/recovery, plus retained limits.

## Sprint 3 dashboard consumer

The frontend now reads health, telemetry, windows, capture-status and monitoring
session metadata through the same restricted Next.js GET relay. Both new GETs
require `session_id` (UUID) and `mode` (LIVE/SIMULATION/REPLAY); omitted or invalid
parameters return 400. Existing POST validation/idempotency is unchanged.

| Extended GET | Response |
| --- | --- |
| `/api/v1/capture-status/?session_id=UUID&mode=LIVE` | Cursor page: `next`, `previous`, `results`; last 24 hours by observed_at, excluding future events; ordered `-observed_at`, `-id`; default limit 50, allowed 1..200, optional cursor |
| `/api/v1/monitoring-sessions/?session_id=UUID&mode=LIVE` | One matching session object; 404 for unknown UUID or wrong mode, identical error; no age filter and no list/discovery |

Capture results expose exactly id, session_id, received_at, observed_at, state,
valid, reason, loss_started_at, gap_ended_at, monitoring_gap_seconds,
recovery_attempts, run_id, mode and interface_name. An unknown capture session or
wrong mode returns an empty page. Session metadata exposes exactly session_id,
source_id, run_id, interface_name, mode, started_at, observation_profile,
schema_version and received_at. Neither endpoint exposes payload_digest or any
unrelated session. Authentication remains deferred; existing local boundaries
and no-store behaviour apply. Database errors still return redacted 503.

The relay fixes limits at 60 samples, 20 windows and 20 status events; session
metadata has no pagination. UI capture state is the latest **reported** event,
not a physical link check; stale/missing/error states remain explicit. Stored gap
seconds are displayed without interpolation or conversion into traffic. No model,
schema or migration changes were needed. See [FRONTEND_SETUP.md](FRONTEND_SETUP.md),
[manual smoke procedure](SPRINT3_SMOKE.md) and the ADR-024 continuation.

## Implemented initial Sprint 2 API - 2026-09-13

Sprint 2 is **PASS for the agreed local backend scope**; see
[operator PostgreSQL evidence and remaining limits](SPRINT2_ACCEPTANCE.md).

This section supersedes the broader planned Sprint 2 routes below for the current
user-authorized scope. Exactly four models: MonitoringSession, TelemetrySample,
TrafficWindow and CaptureStatus. Authentication, batches, sensor registration,
flow endpoints, embedded features/model results, frontend and transport adapter
are deferred. No sensor imports or capture calls exist in the backend.
See [Windows setup](BACKEND_SETUP.md) and ADR-023 in ARCHITECTURE.md.

Base URL: `http://127.0.0.1:8000/api/v1/`. JSON only, trailing slashes required.
Access is deliberately unauthenticated and local-only: fixed localhost hosts,
loopback peer required, Origin/cross-site browser requests rejected, no CORS or
trusted proxy forwarding. This is not authentication against local processes.
Requests are limited to 65,536 bytes; responses use `Cache-Control: no-store`.

| Method | Route | Behaviour |
| --- | --- | --- |
| GET | health/ | Database connectivity; 200 reachable or 503 unavailable |
| POST | monitoring-sessions/ | Register an immutable source/run/session profile |
| POST | telemetry/ | Store one OS-counter aggregate sample |
| POST | windows/ | Store one aggregate ten-second packet window |
| POST | capture-status/ | Store one status/gap event |
| GET | telemetry/?session_id=UUID&mode=LIVE | Recent samples for one session and mode |
| GET | windows/?session_id=UUID&mode=LIVE | Recent aggregate windows for one session and mode |

POST returns the stored object: 201 for a new row, 200 for an identical retry.
Every child record requires a client-generated UUID `id`; sessions require a
client-generated `session_id`. Reuse these IDs when retrying. Normalized metadata
is hashed with full timestamp precision. Changed content under an existing ID
returns 409, as does a new ID reusing `(session_id, observed_at)` for samples/status
or `(session_id, start)` for windows. Objects are not updated by ingestion.
Session/run conflicts also return 409. Integrity is transactional; PostgreSQL
serializes new registrations for the same run with a transaction advisory lock.
Concurrency behaviour on actual PostgreSQL remains to be measured.

GET requires `session_id` and `mode`; omitted/invalid values return 400. Optional
`limit` defaults to 50 and is bounded to 1..200. Responses contain `next`,
`previous`, and `results`; follow returned cursor links. Reads use observation
time (sample `observed_at`, window `end`) within the last 24 hours, newest first.
Old REPLAY data and future timestamps are not current data merely because they
were received recently. A nonexistent session or mismatched mode returns an empty
result. PUT/PATCH/DELETE and general session discovery are not implemented.
The scoped status/session GET extensions above supersede the original Sprint 2
read limitation; the session GET returns 404 rather than an empty page.

Other errors: 400 invalid data/unknown fields, 403 non-local/browser-origin access,
404 unknown route/cursor, 405 method, 413 size, 415 non-JSON, 503 database failure.
Validation errors identify fields; 409 returns `detail`; database failures expose
only a generic error, never passwords. No request body is persisted as a blob.

### Session and shared record fields

Session fields: `session_id`, `source_id`, `run_id` (UUIDs), `interface_name`,
`mode` (LIVE/SIMULATION/REPLAY), `started_at`, `observation_profile` and optional
`schema_version` (only `backend-v1`, default). `received_at` is server-generated.
All listed session fields except `schema_version` are required POST inputs.
Use `interface_name`, not `interface`; include a timezone-aware `started_at`;
`schema_version="1.0"` is unsupported. Unknown/read-only field rejection happens
before ordinary field validation, so correcting `interface` can reveal the
missing timestamp and unsupported version errors next. `session_id` is required
from the client despite the model's UUID default. Do not send `received_at` or
the internal server-generated `payload_digest` (which is also omitted from responses).
For retries, reuse the complete original body, including `started_at`; generating
a new timestamp under the same session ID is conflicting content and returns 409.
Recovery registers a new session ID in the existing run; source, mode, interface
and observation profile must agree across that run. A different profile requires
a new run. This validates declared provenance, not the truth of a source's claims.

All other POSTs require `id`, an existing `session_id`, `run_id`, `mode`, and
`interface_name`. The last three must exactly match the session; they are stored
through the immutable foreign key and returned in responses. Timestamps must be
ISO-8601 with `Z` or an offset, normalized to UTC. Observation cannot precede
session startup; a partial epoch-aligned startup window may start earlier, but
its end must reach the session. `received_at` is always distinct from event time.

### Telemetry fields

`observed_at`, positive finite `elapsed_seconds`, `valid`, nullable `reason`,
four nonnegative cumulative counters (`bytes_sent`, `bytes_received`,
`packets_sent`, `packets_received`), their four `delta_` counterparts, and
`upload_bytes_per_second` / `download_bytes_per_second`. Optional
`measurement_source` is fixed to `OS_COUNTERS`.

For valid samples, deltas and rates are required/non-null; deltas cannot exceed
totals; rates must equal byte delta divided by actual elapsed seconds (numeric
tolerance 1e-6 relative/absolute). Reason is null and elapsed is at most 3 seconds,
matching the existing sensor gap rule. Invalid samples require a nonempty reason
and null deltas/rates; cumulative counters remain real observations, not zeros
substituted for unknown values. NaN/infinity and negative counts are rejected.

### Traffic-window fields

`start`, `end`, `finalized_at`, `processed_at`; `partial`, `valid`, nullable
`reason`; `packets`, `ip_bytes`, `outbound_packets`, `inbound_packets`,
`outbound_bytes`, `inbound_bytes`, `tcp_packets`, `udp_packets`, `flow_count`.
Optional `unknown_packets`, `unknown_bytes`, `other_packets`, `dropped` default
to zero. Optional constants: `measurement_source=PACKET_METADATA`,
`schema_version=backend-window-v1`, `kernel_loss=unknown`.

Windows are epoch-aligned ten-second intervals. Directional counts/bytes and
protocol counts must conserve totals exactly. IP bytes remain distinct from OS
counter bytes. Complete windows require full session coverage, finalization at
end+2 seconds or later, processing at/after finalization, valid=true, partial=false,
null reason, no drops/unknown direction/unsupported protocols. Partial windows
retain their observed aggregate counts, valid=false and a nonempty reason; they
never become valid zero-traffic observations. A complete observed empty window
may contain zeros. No packet payload, raw frame, arbitrary JSON, endpoint inventory,
features or ML score is accepted. `flow_count` counts observed keys, not connections.

`reason` is optional and defaults to null; it is required and nonempty when
`partial=true`. All other non-optional fields listed above, plus the shared
`id`, `session_id`, `run_id`, `interface_name` and `mode`, are required.
`received_at` is generated/read-only; the generated internal `payload_digest`
is neither writable nor returned. IDs must be retained across identical retries.

This aggregate endpoint is not a lossless persistence format for the frozen
seven-feature `host-v1` sensor record. For complete compatible observations its
counts support packets/s, IP bytes/s, outbound byte fraction, UDP fraction and
mean IP packet bytes. It lacks SYN counts and remote-peer data needed for
`tcp_syn_fraction` and `unique_remote_peers`; `flow_count` cannot substitute for
peer count. It also omits the sensor's local-address/capability context. Do not
claim full feature reconstruction or ML eligibility from these rows alone.
The sensor contract remains unchanged; full feature/context persistence requires
a separately scoped contract change. Partial observations have no valid feature
vector, and zero counts in a manual invalid test are not evidence of live idle
capture. Complete LIVE examples require actual measured sensor aggregates.

### Capture-status fields

`observed_at`, `state` (RUNNING/INTERFACE_LOST/RECOVERING/STOPPED), `valid`,
nullable `reason`. Optional `loss_started_at` and `gap_ended_at` default null;
`monitoring_gap_seconds` and `recovery_attempts` default zero and are nonnegative.
Only RUNNING is valid; every other state requires a reason. Loss/recovery times
must be ordered and no later than observation. A recovered RUNNING event may have
reason `interface_recovered`. Events preserve history; no remote capture control
or lifecycle state machine is implied.

### Example local registration and sample (PowerShell)

This example creates explicitly SIMULATION-labelled fixture metadata, not fake
LIVE traffic. Reuse `$sample.id` if retrying the POST. It requires a configured
running PostgreSQL backend; it does not start capture.

```powershell
$api = 'http://127.0.0.1:8000/api/v1'
$session = @{
  session_id = [guid]::NewGuid().ToString()
  source_id = [guid]::NewGuid().ToString()
  run_id = [guid]::NewGuid().ToString()
  interface_name = 'fixture'
  mode = 'SIMULATION'
  started_at = [DateTime]::UtcNow.AddSeconds(-2).ToString('o')
  observation_profile = 'manual-fixture-v1'
}
Invoke-RestMethod "$api/monitoring-sessions/" -Method Post -ContentType 'application/json' -Body ($session | ConvertTo-Json)
$sample = @{
  id = [guid]::NewGuid().ToString()
  session_id = $session.session_id
  run_id = $session.run_id
  interface_name = $session.interface_name
  mode = $session.mode
  observed_at = [DateTime]::UtcNow.ToString('o')
  elapsed_seconds = 1.0
  valid = $true
  reason = $null
  bytes_sent = 100; bytes_received = 200
  packets_sent = 2; packets_received = 3
  delta_bytes_sent = 50; delta_bytes_received = 100
  delta_packets_sent = 1; delta_packets_received = 2
  upload_bytes_per_second = 50.0; download_bytes_per_second = 100.0
}
Invoke-RestMethod "$api/telemetry/" -Method Post -ContentType 'application/json' -Body ($sample | ConvertTo-Json)
Invoke-RestMethod "$api/telemetry/?session_id=$($session.session_id)&mode=SIMULATION"
```

Pruning is explicit and bounded; see BACKEND_SETUP.md. Retry identity is retained
only while the row exists. Global database byte/row admission, automatic retention,
authentication and a sensor uploader are not implemented in this initial slice.

## Historical broader proposal (superseded where it conflicts above)

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
