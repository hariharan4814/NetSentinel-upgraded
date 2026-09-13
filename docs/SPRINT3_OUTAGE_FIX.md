# Sprint 3 historical data retention during backend outage

**Final status: Sprint 3 PASS for the agreed local dashboard scope.** The operator
completed real PostgreSQL-backed readback and outage/recovery checks; see
[SPRINT3_ACCEPTANCE.md](SPRINT3_ACCEPTANCE.md). Pending/repeat statements below
describe the original investigation or reusable test procedure.

The outage regression reproduced loss of data after a successful load. The
polling hook replaced every panel result with the incoming result; a failed
request contains only an error, so the previous data disappeared. Telemetry and
window rendering also used an error-or-content branch that hid historical data.
The selection state itself was not cleared by this code: both UUID and mode
remained selected in the pre-fix regression. A complete page reload/input reset
was not reproduced and is not asserted as a proven symptom of the polling hook.

## Corrected behaviour

Within the mounted session/mode, each failed data refresh now retains its last
successful data alongside the new error. All affected panels show Refresh failed
and label retained records stale/historical. Telemetry and window contents remain
visible instead of being replaced by the error message. Session/capture metadata
remain visible with the same warning. No timestamps or measurement values are
changed, synthesized or advanced.

Backend health is not retained: failure always shows Backend unavailable. Current
rates remain unavailable during failed health/telemetry reads, even if a cached
sample is younger than five seconds. Observation-time freshness continues to age;
successful re-fetch of an old record cannot turn it into current traffic.

Polling/capped backoff continues without re-entering the session, clicking View
session or reloading. Successful responses replace retained data and clear the
error, including successful empty pages. Selection changes still remount the
monitor and discard the old session/mode's data. Retention is only in memory,
bounded to the existing pages; no browser storage or cross-session cache added.
Reloading the whole page still requires selecting a session again.

Gateway security, backend schema/behaviour, sensor and frozen contract are
unchanged. No Sprint 4, ML or commit.

## Regression evidence

Two browser tests failed against the pre-fix build when checking that the loaded
session metadata survived the outage; UUID/mode assertions had already passed.
They now verify successful load -> outage -> automatic recovery for initially
fresh and already-stale samples. They check retained session, status, windows and
telemetry, explicit errors, unavailable current rates, unchanged selection and
stale observation time after reconnection. Four focused unit tests cover retention,
first-load failure, successful empty/replacement responses and observation freshness.

Final checks: **28/28 frontend unit/route tests**, **16/16 production browser
tests**, **38/38 backend tests**, **93/93 sensor tests**. Lint, typecheck,
production build and git diff --check pass. The browser suite includes the prior
real Next gateway regression. Outage transitions use isolated SIMULATION fixtures;
the user's actual Django service was not stopped by the agent.

## Repeat manual outage/recovery smoke

1. Load the updated frontend once with Django running on port 8001. Select the
   existing session UUID and LIVE. Confirm historical telemetry/windows, the
   stored capture event and session metadata have loaded.
2. Stop only Django with Ctrl+C in its runserver terminal. Keep Next.js and the
   browser running; do not refresh or click View session during the outage.
3. Wait for the failed poll. Confirm UUID/mode remain selected, previous records
   remain visible, Backend unavailable and per-panel Refresh failed warnings
   appear, and current upload/download are Unavailable. Partial validity and
   original timestamps/reasons must remain unchanged.
4. Restart Django in that same terminal:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001
```

5. Keep the page open. Recovery occurs on the next poll (up to the 30-second
   backoff plus request time). Confirm Backend reachable and cleared refresh
   errors without reselecting or reloading. Old telemetry/capture events remain
   stale; restored connectivity is not new sensor evidence. A genuinely empty
   successful response may replace old cached records, for example after expiry.

Starting the dashboard if needed before step 1:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm run dev
```

Do not start a duplicate server if it is already running. See
[SPRINT3_SMOKE.md](SPRINT3_SMOKE.md) for initial configuration. Manual sign-off
requires repeating these observations on the user's real PostgreSQL/Django data.
