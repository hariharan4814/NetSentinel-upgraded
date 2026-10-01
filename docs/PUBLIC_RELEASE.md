# Public connection helper — release notes

## Product and scope

Implemented 2026-10-01 following the user's explicit upgrade request and choice
of everyday internet troubleshooting. The original research system is preserved;
the public homepage is a new practical helper with vanilla CSS glass surfaces.
See [implementation plan](../plan.md), [design plan](../designplan.md) and ADR-028.

Features: bounded/cancellable HTTP checks, real response chart and readings,
four guided troubleshooting plans, optional browser history and comparison,
deletion, text report downloads, manual-speed transfer calculator and a how-to /
privacy guide. No new dependency, copied repository, account or external API.

## Local use

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm ci
npm run build
npm run start
```

Home: `http://127.0.0.1:3000`. Advanced original monitor: `/local` (requires the
existing local backend/data). The public helper itself does not require either.
All services remain bound to loopback by default. LOCAL browser measurements
do not test internet access. Use the published hostname for LIVE HTTP checks.

## Public package

`npm run build:public` builds from an explicit public-source allowlist into
`frontend/.public-build/out`, then copies it to `public-release/dist`. It excludes
the private dashboard, relay, sensor, ML, database and local environment files.
The script refuses to reuse populated generated output directories. Before a
rebuild, review and remove only `frontend/.public-build` and
`public-release/dist`, preserving `public-release/.git` and `.openai`.
Do not delete source, user data or the main repository's .git directory.

Sites manifest: `.openai/hosting.json` in the separate `public-release` checkout,
with `static.directory` set to `dist`. Reuse project
`appgprj_6abe7cb737b48191aecdf0a81f9caf4e` on subsequent publication; do not create
a duplicate. The public artifact is about 0.7 MB as a tar archive. Only that
checkout's public files are sent to hosting. The main repository is not pushed.

During this run the bundled Sites helper disappeared from the installed plugin
cache after registration. A temporary fallback used hidden-stdin credentials,
repository-scoped Git authentication in child-process memory, exact remote-commit
verification and `git archive` of only `.openai/hosting.json` and `dist`. No
credentials were written to files or embedded in Git remotes. The hosting service
requires a supported static directory name such as `dist`; the initial `site`
directory and a string-form manifest were rejected and corrected.

## Actual verification

| Check | Result |
| --- | --- |
| Frontend unit/route tests | 37 passed (8 new public-contract tests + 29 existing) |
| Production browser regression | 24 passed, 1 private-data smoke test skipped |
| Existing offline sensor tests | 93 passed; no live packet capture attempted |
| ESLint | Passed, zero warnings |
| TypeScript | Passed, including public export compilation |
| Original Next production build | Passed; routes `/`, `/local`, restricted backend relay |
| Public static production build | Passed; only `/` and framework not-found route |
| Actual public artifact on loopback | Homepage renders; eight requests complete as LOCAL; no browser console errors |
| Public artifact boundary | `/local` and `/api/backend/health` both return 404 |
| Browser review | Desktop and narrow mobile layout, no body horizontal overflow, planner error state, checklist, guide |
| Whitespace validation | `git diff --check` passed |
| Existing user modification | `frontend/next-env.d.ts` restored byte-for-byte after build tooling regenerated it |

The first full browser run had one failure because the old private Session 4
smoke test unconditionally targeted a stopped server on port 3000. It now targets
`/local` and is explicitly opt-in with `NETSENTINEL_LIVE_SMOKE=1`. Its original
data assertions are preserved. No real private-session pass is claimed.

The test runners needed the installed Windows runtimes outside the restricted
shell. Sensor tests warned that a libpcap provider was unavailable; fixture tests
passed, but that does not establish current Npcap availability or live capture.
Backend database/ML suites, long-duration hardware runs, calibrated performance,
and multi-browser accessibility audits were not rerun or claimed in this change.

## Limits and operating notes

- Eight responses from one site are a short snapshot. They cannot establish ISP
  uptime, speed, Wi-Fi strength, packet loss or the cause of a problem.
- The 300 ms median / 150 ms range advice is a transparent product heuristic,
  not a validated quality guarantee. Complete failures may be site/browser related.
- Browser history is off by default; if enabled, it is capped at 10 records for
  7 days. Expiration is applied on load or history updates, not by a background job.
- Shared browser profiles share saved history. Downloads remain until deleted.
- Hosting sees normal HTTP request metadata and may retain provider access logs.
  No third-party analytics, fonts or trackers were added by this application.
- This is a small public MVP. It does not provide a calibrated throughput test,
  cloud packet capture, multi-user private monitoring or automated network fixes.

## Publication status

**Published successfully, 2026-10-01.** Native deployment status is `succeeded`,
and site access mode is `public`.

Live URL: https://netsentinel-connect.hariharan4814.chatgpt.site

- Project: `appgprj_6abe7cb737b48191aecdf0a81f9caf4e`
- Version: `appgprj_6abe7cb737b48191aecdf0a81f9caf4e~appgver_baa3cdda460081919f77ea1f3ca29f4b`
- Deployment: `appgdep_6abe8837595c81919a323fcfc5a33801`
- Public-source commit: `8716c17203ebc7a011d3f46aea9815f131265b64`
- Accepted archive: 716,800 bytes, 26 files; SHA-256
  `c0f0f4da9a525e760c4b52bcceb5f068b507e35d347aebd6daccdd229ebcbdcb`

Native hosting confirmed publication. Browser QA was performed against the local
production app and exact static artifact; no hosted performance calibration or
fresh live sensor capture is claimed. No recurring automation was created because
the utility runs only at the visitor's request.
