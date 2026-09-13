# Sprint 3 gateway Host normalization fix

**Final status: Sprint 3 PASS for the agreed local dashboard scope.** The operator
completed real PostgreSQL-backed readback and outage/recovery checks; see
[SPRINT3_ACCEPTANCE.md](SPRINT3_ACCEPTANCE.md). Pending/repeat statements below
describe the original investigation or reusable test procedure.

## Proven cause

Installed Next.js 16.3.5 normalizes loopback names in NextURL to `localhost`.
Constructing its actual NextRequest for the browser's URL reproduces:

```text
request.url = http://localhost:3000/api/backend/health
Host        = 127.0.0.1:3000
Origin      = null
```

The old guard required `Host === new URL(request.url).host`, which is false.
If Origin was present it was also compared against the normalized origin rather
than the wire Host origin. This affects development and production. The installed
implementation is `node_modules/next/dist/server/web/next-url.js`, parseURL.
Previous unit tests constructed plain Request, and browser tests intercepted all
gateway requests, so neither reproduced NextRequest normalization.

Missing Origin was not the defect: the old guard already allowed it. Same-origin
GET/HEAD can legitimately omit Origin; see the [HTTP Origin documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin).
Our no-referrer response policy also means Referer can be absent. Local PowerShell
GETs were not intentionally prohibited; they failed the same Host comparison.
These headers do not authenticate local processes.

## Small fix and preserved boundary

Only application change: `frontend/src/lib/gateway.ts`, localRequest.

- Strictly validate wire Host as localhost, 127.0.0.1 or [::1], optionally with a
  valid port. Reject credentials, paths, malformed authorities and other hosts.
- Require an HTTP local request URL and matching port. Allow the known NextURL
  localhost normalization; do not treat arbitrary Host/URL mismatches as valid.
- Compare a supplied Origin to the validated **wire Host** origin. localhost and
  127.0.0.1 are not interchangeable browser origins; scheme/port differences fail.
- A supplied Referer must also match that origin. Neither Origin nor Referer is
  mandatory for a GET. Reject cross-site/same-site or malformed Sec-Fetch-Site.
- Forwarded and X-Forwarded-* headers are not trusted to select the authority or
  authorize a request. They cannot rescue a hostile Host or Origin.
- Retain loopback-only server bindings, GET-only routes, fixed resource allowlist,
  bounded query construction, loopback upstream, no redirects, no browser header
  forwarding and no-store responses. No CORS exemption or public listener added.

No Django/schema/migration/sensor change in this bug fix. No Sprint 4 or commit.

## Verification and evidence boundaries

- Frontend unit/route tests: **24/24** pass, including actual NextRequest tests
  for Origin present/absent, localhost/IPv6 validation, malformed/mismatched Host,
  cross-origin and non-local sources, Referer and forwarded-header handling.
- Production browser suite: **14/14** pass. Two new tests exercise the real Next
  route without browser interception, with an isolated loopback health upstream:
  legitimate no-Origin browser GET returns 200, unknown resources 404, hostile
  Origin 403, POST 405. Existing dashboard fixture tests remain unchanged.
- Development real-route suite: **2/2** pass against the operator's existing
  server at port 3000; browser gateway health returned 200. The existing server
  was reused and left running. A first attempt at a second dev server was refused
  by Next's same-directory lock; no process was killed or lock deleted.
- Backend **38/38**, sensor **93/93**, lint, typecheck, production build and
  git diff --check pass. These are the current totals; earlier docs retain the
  historical pre-fix runs.

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm test
npm run lint
npm run typecheck
npm run build
npm run test:e2e
npx playwright test --config playwright.dev.config.ts
```

Production tests use ports 3100/3103. Development tests reuse port 3000 if already
running (including its current upstream configuration); otherwise they start a
local dev server with the fixture upstream. Both test variants are read-only.
The dev suite checks gateway routing/health, not complete stored session content.

## Repeat manual smoke

Repeat [SPRINT3_SMOKE.md](SPRINT3_SMOKE.md) after refreshing/restarting Next as
needed. Verify all dashboard panels against the direct Django responses, including
old RUNNING being labelled stale. No-Origin PowerShell gateway reads should now
work as well. The successful automated dev health check does not replace that
full manual PostgreSQL/data-panel comparison or prove continuous sensor delivery.
