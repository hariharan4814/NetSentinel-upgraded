# Sprint 2 backend acceptance - 2026-09-13

**PASS for the agreed four-model local backend scope.** This sign-off does not
certify full sensor-to-backend feature preservation, deployment, authentication
or the broader historical roadmap. Sprint 3 is not started. Nothing is committed
by this sign-off task.

## Scope and evidence

The user's implementation scope supersedes the older broader Sprint 2 proposal:
Django REST Framework, environment-configured PostgreSQL, exactly
MonitoringSession, TelemetrySample, TrafficWindow and CaptureStatus; seven REST
operations; typed aggregate metadata, provenance, timestamps, validity/reasons,
validation, migrations, retry/conflict handling and tests. SQLite is test-only.
No payloads, auth, frontend, ML, Celery, Redis, WebSockets, alerts or deployment.

| Acceptance item | Evidence / result |
| --- | --- |
| PostgreSQL configuration and migrations | Operator reports PostgreSQL 17 running locally, dedicated role/database `netsentinel`, all three migrations applied successfully |
| Health GET | Operator reports `status=ok`, `database=reachable` on port 8001 |
| Session POST | Operator reports success |
| Telemetry POST and identical retry | Operator reports stored row returned on retry without duplicate |
| Recent telemetry GET by session/mode | Operator reports stored row returned |
| Window POST | Operator reports success for an explicitly invalid partial manual test window; not evidence of complete live capture |
| Recent windows GET | Implemented and covered by automated backend tests; no manual PostgreSQL GET result supplied |
| Capture-status POST and identical retry | Operator reports successful POST and same stored record on retry; API acceptance alone does not prove capture is running |
| Validation, conflicts, provenance, gaps and bounds | 31 automated backend tests pass with SQLite; PostgreSQL concurrency/negative-path coverage is not claimed |
| Independent proven sensor | All 93 sensor tests pass; source/tests/dependencies and frozen feature contract unchanged against Sprint 1 commit `ea8819a` |

Applied migration names reported by the operator:

- `monitoring.0001_initial`
- `telemetry.0001_initial`
- `telemetry.0002_trafficwindow_window_session_end_idx`

Manual evidence above comes from the user's explicit report, not independently
captured HTTP transcripts or a new live run by the agent. No private telemetry,
credentials or captures are included. These are persistence/API checks, not a
claim that manual records form a scientifically valid live baseline.

## Final checks run by the agent

From the repository root:

```powershell
.\.venv-backend\Scripts\python.exe backend/manage.py test backend/tests --settings=config.test_settings -v 1
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor
.\.venv-backend\Scripts\python.exe backend/manage.py check
.\.venv-backend\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
git diff --check
```

Backend: **31/31 passed** (0.631 seconds). Sensor: **93/93 passed** (2.957 seconds).
The sensor's injected missing-driver and operator-stop messages are expected test
paths. Django check: no issues. Migration consistency: no changes detected.
These two commands used normal PostgreSQL settings, not test settings.
Whitespace check: passed. No schema or application code changed for sign-off.

## Explicit deferred integration and operational limits

- TrafficWindow stores aggregates sufficient for only five compatible feature
  calculations. It omits remote-peer and SYN inputs for `unique_remote_peers`
  and `tcp_syn_fraction`, plus local-address/capability context. `flow_count`
  cannot substitute for peer count. This is not a pass for lossless seven-feature
  persistence or ML eligibility. The frozen Sprint 1 `host-v1` contract remains
  unchanged; full context/feature persistence needs separately authorized work.
- No sensor upload adapter or full sensor-to-PostgreSQL live integration is
  certified. Partial/invalid test windows have no valid feature vector and are
  not measured idle traffic. Sprint 1's independent outage evidence is retained.
- Authentication is intentionally deferred. Bind only to loopback; the local
  peer/Host/Origin restrictions do not authenticate local processes. Do not
  expose the API through a network listener or reverse proxy.
- Actual PostgreSQL concurrent ingestion, race/conflict stress, throughput and
  full negative-path tests remain unmeasured. Sequential retry evidence is not
  concurrency evidence. Recent-window PostgreSQL readback is an optional remaining
  manual cross-check; automated coverage satisfies the agreed endpoint scope.
- Reads are bounded to 24 hours and pages of at most 200 records. Pruning is
  explicit, at most 1,000 expired rows per record table per invocation; sessions
  remain. No automatic retention, global row/byte admission limit or durable
  upload spool exists. Idempotency lasts only while the record is retained.

These limitations are disclosed boundaries of this accepted backend scope, not
hidden passes for deferred requirements. The next task is user review and commit
of Sprint 2; no subsequent sprint is authorized by this document.
