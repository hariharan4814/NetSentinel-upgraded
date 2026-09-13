# Sprint 3 final acceptance

**PASS for the agreed local Next.js dashboard and scoped read-integration scope.**
The operator's manual PostgreSQL-backed browser smoke test, including Django
outage and automatic recovery, closes the previously pending manual gate. This
does not certify continuous sensor uploading, physical link measurement,
authentication, full feature persistence or measured end-to-end latency.
Sprint 4/ML is not started. No commit is performed by the sign-off task.

This report supersedes earlier PARTIAL/pending statements in Sprint 3 setup,
smoke and bug-investigation documents. Those documents retain implementation
history and reproducible procedures; their older test totals are historical.

## Agreed scope review

| Gate | Evidence / result |
| --- | --- |
| Next.js, TypeScript, responsive local dashboard | Overview, telemetry chart/table, window table, capture/interface and session sections implemented; production build/typecheck/lint and desktop/mobile browser coverage pass |
| Existing Django boundary and server-only URL configuration | Restricted local GET relay; no component backend URLs, direct database access or sensor imports; gateway allowlist/Host/Origin regressions pass |
| Minimal missing read integration | Existing capture-status route extended with bounded session/mode GET; monitoring-sessions GET returns one scoped manifest or 404; no models/migrations or POST semantics changed |
| Provenance and measurement presentation | LIVE/SIMULATION/REPLAY stay explicit; counts/rates/UTC/interface/session identity displayed from records; manual Ethernet 3 LIVE readback verified |
| Invalid, partial, stale and missing observations | Manual stale telemetry/current unavailable rates, partial invalid window and stale RUNNING event verified; automated null/zero/freshness/provenance tests pass |
| Capture/gap and full session metadata | Stored status, validity, reason, timestamps, gap/recovery fields and session manifest implemented/tested; manual capture/session readback verified; physical link remains unavailable |
| Reasonable polling and failure handling | Non-overlapping two-second polling with bounded backoff, cancellation and mode/session isolation tested; loading/empty/errors covered |
| Outage retention and reconnect | Manual loss of Django retains UUID/mode/history, marks errors/staleness, hides current values, and recovers without reload/re-entry |
| Preserve prior sprints and exclusions | 38 backend and all 93 sensor tests pass; no model/migration, proven sensor or frozen feature change; no auth, ML, alerts, Celery, Redis or WebSockets added |

These are the user's approved dashboard gates, including the explicitly scoped
GET additions. The older roadmap's continuous live display/latency and broader
flow presentation proposals are not silently claimed complete. This dashboard
shows stored aggregates and observed flow-key counts, not per-flow endpoint
details or proven transport connections.

## Operator-verified manual smoke evidence

Source: the user's explicit final smoke-test report. These observations were
made against their running local PostgreSQL-backed Django and browser dashboard;
they are not simulated browser fixtures or a new live sensor run by the agent.
No private records, screenshots, credentials or packet captures are committed.

Before outage:

- Stored session loaded; interface Ethernet 3 and mode LIVE displayed.
- Historical telemetry was labelled stale; current upload/download unavailable.
- Partial invalid TrafficWindow clearly labelled.
- Stored RUNNING CaptureStatus shown as stale, not as proof of current capture.
- Full session metadata loaded; physical interface link state stayed unavailable.
- Gateway successfully served the dashboard data.

During Django outage, the operator observed these messages:

> Backend unavailable or request timed out. Retrying with bounded backoff.

> Refresh failed: Backend unavailable or request timed out. Showing stale historical data from the last successful load; current state is unavailable.

Historical records stayed visible, selected session/mode stayed intact, current
state/rates were unavailable and the page did not reset.

After Django restart, the dashboard automatically returned to Backend reachable.
No browser refresh or session re-entry was required. This is a **manual smoke
PASS** for stored-data readback and backend outage/recovery, not a latency or
continuous capture delivery benchmark.

## Final verification run

| Check | Result |
| --- | --- |
| Frontend unit/route tests | 28/28 passed |
| Frontend production browser suite | 16/16 passed, including real gateway routing and outage/recovery regressions |
| ESLint | Passed, zero warnings |
| TypeScript | Passed |
| Next.js production build | Passed |
| Backend automated tests | 38/38 passed, SQLite test settings |
| Existing sensor suite | 93/93 passed |
| Django check | No issues, normal PostgreSQL settings |
| makemigrations --check --dry-run | No changes detected, normal PostgreSQL settings |
| git diff --check | Passed |

The original 31 backend tests remain included, including ingestion retries and
conflicts. Browser tests use isolated fixtures for outage/measurement assertions;
the independent manual evidence above supplies the real PostgreSQL browser check.
The sensor suite's injected driver-error/stop messages are expected test paths.

## Retained limitations

1. **No automatic sensor uploader.** Opening the dashboard does not start capture
   or stream sensor output. Continuous sensor-to-dashboard delivery, throughput
   and numerical latency targets remain unmeasured integration work.
2. **No authentication.** Both servers must stay loopback/local-only. Host/Origin
   checks are not authentication against local processes; no LAN/proxy deployment
   is accepted. Django's security restriction remains intact.
3. **No physical link-state measurement.** Stored RUNNING is a reported capture
   event, not a physical interface check or heartbeat. Old reports remain stale.
4. **Session selection requires UUID and mode.** There is no general session
   discovery UI/API. Retained dashboard data is in memory within that selection;
   a full page reload still requires selecting a session again.
5. **Seven-feature persistence is incomplete.** TrafficWindow retains inputs for
   only five compatible calculations; peer and SYN inputs for unique_remote_peers
   and tcp_syn_fraction plus full capture context remain absent. No ML eligibility
   or lossless host-v1 persistence is claimed. The Sprint 1 contract is unchanged.
6. **Bounded history and operational limits remain.** Reads cover recent 24-hour
   observation pages; old/future records do not become current via receipt time.
   Pruning is manual, idempotency lasts while rows are retained, and PostgreSQL
   concurrency/stress testing remains unmeasured. ESLint 9 is pinned for the
   current Next React-plugin compatibility; its unsupported maintenance status
   remains documented in FRONTEND_SETUP.md.

The next action is user review and commit of Sprint 3. No later sprint is
authorized by this sign-off.
