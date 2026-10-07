# Sprint 3 dashboard (Windows / PowerShell)

## AI Lab interface — 2026-10-05

`/lab` is the authenticated local simulation workbench. It shares the existing
operator sign-in with `/local`; a separate server-only `NETSENTINEL_LAB_TOKEN`
authorizes job creation/cancellation. Never place the worker key in Next.js.
The fixed `/api/lab/jobs` relay accepts bounded settings, UUIDs and no commands
or arbitrary URLs. Run a lab backend and `.venv-lab` worker as described in
[AI_LAB_CONTRACT.md](AI_LAB_CONTRACT.md); the standalone launcher uses a separate
SQLite store, while the original research stack retains PostgreSQL.

The studio generates metadata, trains and evaluates real models in that worker.
The interface displays actual stages, retained experiments, recorded-window
playback with optional truth, missing observations, comparative metrics,
confusion matrices, selected SHAP evidence and semantic PDF/JSON downloads.
No metrics appear before a completed result. Every result is SIMULATION;
statistical deviation is not proof of attack. Generated workloads send no packets.

The vanilla CSS at `src/app/lab/lab.css` is scoped to the lab, with translucent
surfaces, visible keyboard focus, semantic tables and responsive navigation.
The static public allowlist excludes `/lab`, `/local` and all API routes.
The browser fixtures in `tests/browser/lab.spec.ts` are explicitly synthetic
UI checks; actual model/worker integration must be verified separately.

Validation commands: `npm test`, `npm run lint`, `npm run typecheck`,
`npm run build`, `npm run test:e2e`. Preserve local `next-env.d.ts` edits if
Next regenerates this file. Detailed current evidence belongs in `plan.md`.

**Current entry points (2026-10-01):** `/` now serves the public connection helper
and needs no backend. The original monitoring dashboard described below is at
`/local`; use `http://127.0.0.1:3000/local` for its UUID/mode workflow. The
public-only export excludes `/local` and all API routes. See [release guide](PUBLIC_RELEASE.md)
and ADR-028. Remote Google font loading was removed in favor of system fonts.

Gateway smoke-test fix: [NextRequest Host normalization](SPRINT3_GATEWAY_FIX.md).
Local browser GETs may omit Origin/Referer. Supplied values are checked against
the validated wire Host, not Next's normalized localhost URL. Gateway-fix regression
totals were 24 unit/route, 14 production browser and 2 dev real-route tests. The
earlier verification counts below describe the read-integration implementation.

The Next.js/TypeScript dashboard is implemented against the existing read API.
The scoped capture-status and session GET extensions now provide recorded status,
gaps/recovery and full session metadata. **Sprint 3 PASS**: the operator verified PostgreSQL-backed browser readback,
Django-outage retention and automatic recovery. See [final acceptance](SPRINT3_ACCEPTANCE.md)
and the [repeatable smoke procedure](SPRINT3_SMOKE.md). No backend schema,
sensor, feature contract, authentication or ML behaviour is changed. Sprint 4
is not started and this implementation is not committed by the agent.

## Start locally

Node.js 24.19.0 and npm 11.17.0 were present and used. The project requires Node
22+; use the tested Node 24 environment where possible. Next.js 16.3.5, React
19.3.0 and TypeScript 5.9.3 are pinned; transitive versions are in package-lock.json.
No remote fonts, CDN assets or third-party analytics are loaded.

Keep the existing Django server running on loopback in its own terminal:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001
```

Do not start a second copy if port 8001 is already serving Django. In another
PowerShell terminal:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm ci
if (-not (Test-Path -LiteralPath .env.local)) {
    Copy-Item -LiteralPath .env.example -Destination .env.local
}
npm run dev
```

Open `http://127.0.0.1:3000`. Enter an existing session UUID and its exact
LIVE/SIMULATION/REPLAY mode, then choose **View session**. Mode selection only
filters observations; it neither creates data nor starts capture. No session
IDs are hardcoded, persisted in browser storage or sent to third parties.

`frontend/.env.local` has one server-only variable:

```dotenv
BACKEND_API_BASE_URL=http://127.0.0.1:8001/api/v1/
```

It must be a loopback HTTP URL ending in `/api/v1/`, with no credentials, query
or fragment. Change the port here if necessary, then restart Next.js. Do not
use a NEXT_PUBLIC variable or put URLs into components. Missing/malformed
configuration produces a visible API error. `.env.local` is ignored by Git.

Production build for local use:

```powershell
npm run build
npm run start
```

Both development and production scripts bind to `127.0.0.1`. Authentication
remains intentionally deferred. Do not expose either service on the LAN or
through an external reverse proxy. Local processes are not authenticated.

## Structure and API boundary

- `src/app`: App Router page, layout, responsive CSS and a read-only API route.
- `src/components/dashboard.tsx`: overview, telemetry chart/table, windows table,
  capture/interface availability and session summary sections with anchor navigation.
- `src/lib/contracts.ts`: response shape/provenance checks, safe numeric handling,
  UTC formatting and explicit observation freshness policy.
- `src/lib/use-monitor.ts`: bounded polling, cancellation, backoff and panel errors.
- `src/lib/gateway.ts`: local URL/request validation and fixed query construction.
- `tests`: Node unit/route tests and Playwright browser scenarios with isolated
  synthetic SIMULATION fixtures; browser tests write no Django records.

The browser calls same-origin GET `/api/backend/health`, `/api/backend/telemetry`
and `/api/backend/windows`, plus `/api/backend/capture-status` and
`/api/backend/monitoring-sessions`. The Next server issues GETs to the corresponding
Django routes. There is no generic proxy, POST forwarding,
capture call, Django ORM access or direct database connection. Browser cookies,
Origin and forwarding headers are not passed upstream. Django's existing local
client checks remain unchanged. The relay rejects non-local Host and cross-origin
requests, restricts upstream to loopback and refuses redirects. It does not add
identity authentication. Responses and fetches use no-store.

All four scoped reads require `session_id` and `mode`. The relay fixes limit=60
for telemetry and limit=20 for windows/status; the backend applies its
last-24-hours filter to observations. Session GET returns one object without
an age filter; unknown UUID/mode pairs return 404.
This first dashboard displays only the newest page, not an unlimited history.
Unexpected response shapes, mode/session mismatches and integers unsafe for
JavaScript representation fail explicitly instead of silently corrupting values.

## Polling and observation semantics

Each cycle makes five parallel reads. A single next cycle is scheduled two
seconds after completion, so slow requests cannot overlap. The server timeout
is four seconds and the client timeout seven. Failures back off to 4/8/16/30
seconds; successful cycles reset to two seconds. Hidden tabs pause requests;
visibility/online events resume. Selection changes remount the monitor, clear
old data and abort old requests. There is no cross-mode cache or local persistence.

A **five-second display freshness limit** hides current rates for old/future
observations; this is a UI policy, not a changed sensor acceptance threshold or
proof of capture health. Receipt time never makes an old sample current. Invalid
or unavailable samples display Unavailable, not zero. Valid measured zero is
shown as zero. The historical chart draws individual points, never interpolation
across missing intervals; invalid records are marked separately. Exact historical
rates remain in an accessible table with timestamps and reasons.

OS cumulative packet counters are labelled as such, not presented as session
totals. OS counter bytes and window IP bytes are separate. Partial windows retain
their invalid badge, reason and aggregate counts; zero partial counts are not
measured idle capture. All timestamps are UTC and provenance stays visible.

## Capture and session presentation

Capture shows latest reported RUNNING/INTERFACE_LOST/RECOVERING/STOPPED, validity,
observed UTC timestamp, reason, loss/gap timestamps, recorded gap seconds and
recovery attempts. Missing status is Unavailable; absent status is not zero gap.
A stored 0 s is labelled as a recorded event value, never a traffic value. An
invalid capture event at/after the latest sample suppresses current rate cards;
historical samples retain their original values. Gap duration is never advanced
by a browser timer. Physical interface link state remains Unavailable because
no stored field proves it.

Status reports older than **15 seconds** are labelled stale, with current state
unavailable; the latest historical state remains visible. This is a conservative
UI display policy, not a heartbeat assertion or changed sensor threshold. Future
reports are likewise not current proof. Failed refreshes retain the last loaded
data with explicit error/stale-history warnings; health is never cached as
reachable. Successful responses replace old data, including empty pages.
Loading/paused states are explicit. Session metadata is an immutable manifest,
not a capture heartbeat: interface, mode, session/run/source IDs, start time,
profile and schema version come from the matching session GET.

## Remaining limitations

No session discovery: the user still supplies a UUID and mode. Historical status
reads are bounded to 24 hours, not a guarantee of continuously reported state.
No sensor uploader or full live refresh/latency evidence is supplied by this
change. Five-feature aggregate persistence remains unchanged; no missing peer,
SYN or capability context is invented. No physical link state or authentication
is implemented; both servers must remain loopback-only.

The missing scoped read APIs have now been implemented. Manual frontend-to-Django
smoke verification now passes; see [SPRINT3_ACCEPTANCE.md](SPRINT3_ACCEPTANCE.md).
Use [SPRINT3_SMOKE.md](SPRINT3_SMOKE.md) to reproduce the checks.
An optional server-start command was blocked in the earlier frontend session;
no new manual live smoke result is claimed here.

## Verification

Latest outage regression: **28/28 unit/route and 16/16 browser tests** pass;
see [outage fix and manual repeat steps](SPRINT3_OUTAGE_FIX.md). Earlier totals
below describe the initial read-integration checks.

```powershell
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Passed: lint with zero warnings, TypeScript, production build, **18 unit/route
tests**, **12 browser tests** using installed Microsoft Edge headlessly. Browser
coverage includes loading, empty/error, measured zero, invalid/partial data,
mode changes with in-flight requests, and mobile overflow. Desktop and 390px
mobile screenshots were inspected. Browser tests use port 3100 and manage their
own loopback server; build first. Edge is only needed for browser tests.

ESLint 9.39.5 is pinned because the current Next React lint plugin fails under
ESLint 10 (`contextOrFilename.getFilename is not a function`). npm marks ESLint 9
unsupported; upgrading the compatible lint toolchain remains a maintenance item.
The installed dependency audit reported zero vulnerabilities. Official Next.js
[installation guidance](https://nextjs.org/docs/app/getting-started/installation)
separates lint from build; both were run explicitly.

Existing backend plus focused read tests: **38/38**; sensor **93/93** pass.
Only backend view/read plumbing and tests changed; models, migrations, ingestion
serializers/idempotency and the sensor/frozen contract remain unchanged.
`git diff --check` passes. Sprint 2's operator PostgreSQL evidence is preserved
as historical evidence, not replaced by these mocked browser tests.
