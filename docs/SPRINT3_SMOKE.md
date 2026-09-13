# Sprint 3 scoped read integration and manual smoke test

**Final status: Sprint 3 PASS for the agreed local dashboard scope.** The operator
completed real PostgreSQL-backed readback and outage/recovery checks; see
[SPRINT3_ACCEPTANCE.md](SPRINT3_ACCEPTANCE.md). Pending/repeat statements below
describe the original investigation or reusable test procedure.

Repeat this procedure after the [gateway Host normalization fix](SPRINT3_GATEWAY_FIX.md).
The real dev-server browser health check now passes. Local PowerShell reads are
also supported; the old rejection was a bug, not a browser-only policy. Full
manual panel/data comparison remains required before smoke sign-off.

Code/tests are ready for manual local PostgreSQL verification. This document
does not claim the smoke test has already passed. No model, migration, sensor,
ingestion validation or idempotency change is included. No commit or Sprint 4/ML.

## Implemented continuation

- CaptureStatus GET: required session UUID/mode, scoped recent cursor page,
  last 24 hours by observed_at, newest first, default 50 / maximum 200.
- MonitoringSession GET: required session UUID/mode, one matching metadata
  object without age expiry; unknown/mismatched scope returns 404.
- Shared bounded-read code extracted from telemetry views into common/reads.py.
  POST handling and serializers are unchanged; no general session list exists.
- Dashboard reads both endpoints and displays recorded status, validity, reason,
  loss/gap timestamps, gap seconds, recovery attempts and full session identity.
  Missing/error values stay unavailable. Status is historical after the 15-second
  UI freshness limit; it is not proof of physical interface link state.

Verification: backend **38/38**, frontend unit/route **18/18**, browser **12/12**,
sensor **93/93**. Lint, typecheck, production build, normal-settings Django check,
migration consistency and git diff --check pass. Browser fixtures are isolated
SIMULATION data, not PostgreSQL/live sensor evidence. The original 31 backend
tests (including POST retries/conflicts) and all 93 sensor tests remain passing.

## Terminal 1: Django

Run from the repository root. Keep PostgreSQL 17 running and the existing .env.
If Django is already running with autoreload, use it; do not start a second server
on the same port. Otherwise:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel
.\.venv-backend\Scripts\python.exe backend/manage.py check
.\.venv-backend\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001
```

No new migration needs applying for this change.

## Terminal 2: dashboard

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm ci
if (-not (Test-Path -LiteralPath .env.local)) {
    Copy-Item -LiteralPath .env.example -Destination .env.local
}
npm run dev
```

The existing `.env.local` must set
`BACKEND_API_BASE_URL=http://127.0.0.1:8001/api/v1/`. Restart Next after changing
it. Both services stay on loopback; authentication remains deferred.

## Terminal 3: compare read responses

These commands only read the existing session; they create no traffic or events.

```powershell
$sessionId = '11111111-1111-1111-1111-111111111111'
$mode = 'LIVE'
$scope = "session_id=$sessionId&mode=$mode"
$django = 'http://127.0.0.1:8001/api/v1'
$dashboard = 'http://127.0.0.1:3000/api/backend'

Invoke-RestMethod "$django/health/"
$storedSession = Invoke-RestMethod "$django/monitoring-sessions/?$scope"
$storedStatus = Invoke-RestMethod "$django/capture-status/?$scope&limit=20"
$displaySession = Invoke-RestMethod "$dashboard/monitoring-sessions?$scope"
$displayStatus = Invoke-RestMethod "$dashboard/capture-status?$scope"

$storedSession | Format-List
$displaySession | Format-List
$storedStatus.results | Select-Object -First 1 | Format-List
$displayStatus.results | Select-Object -First 1 | Format-List
```

Confirm source/run/session IDs, interface, mode, start time and profile match.
Compare latest status ID, state, validity, observed time, reason, recorded gap and
recovery attempts; a newly ingested event between reads can legitimately differ.
404 means no matching session/mode. An empty status page means no status observed
in the last 24 hours; do not insert fabricated LIVE events to make the test pass.

Open `http://127.0.0.1:3000`, enter the UUID and LIVE, and select View session.
Confirm the session panel matches the GET object and the capture panel matches
the latest stored event. Old events must be marked stale, not claimed current.
Physical interface link state must stay Unavailable. Null reasons/timestamps
stay unavailable; stored zero gap seconds never imply zero network traffic.
Existing invalid partial manual windows must retain their validity and reason.

To check outage handling, stop only the Django development server with Ctrl+C.
Within the request timeout/next poll, the dashboard must show unavailable/errors
rather than current zero rates. Selection and previously loaded historical data
must remain visible with refresh-failed/stale-history warnings. Do not reload or
reselect during this check. See [the outage regression](SPRINT3_OUTAGE_FIX.md).
Restart the same runserver command; polling must
recover within its capped 30-second backoff plus request time. Do not stop or
modify the sensor for this check. No live status is inferred from backend health.

Report actual observed results, including empty/stale states. Current capture
state/continuous rate evidence requires genuine recent sensor emissions through
a separately implemented uploader; that remains outside this read-only change.
