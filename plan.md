# NetSentinel public product upgrade

Prepared 2026-10-01, before implementation. The current user request authorizes
implementation and public launch, superseding the old documentation-only stage
and academic-only presentation scope. Target audience confirmed by the user:
everyday people troubleshooting slow or unreliable internet.

## 1. Repository assessment

The repository contains a Next.js 16/React 19 frontend, modular Django backend,
PostgreSQL contracts, independent Windows sensor and offline ML tools. It is
substantially implemented despite AGENTS.md's historical Sprint 0 heading.
Existing documentation records past verification; those totals are historical,
not evidence that checks passed in this upgrade.

The current homepage asks for a session UUID and exposes model thresholds,
capture windows and technical provenance. This is useful for a local research
operator but offers an ordinary visitor little help without installing Python,
Npcap and PostgreSQL. The backend and Next relay are intentionally local and
unauthenticated. Exposing that system publicly is not a safe deployment path.
There are contradictory historical status statements across documents. New
decisions below take precedence for the public product only.

Existing user change: frontend/next-env.d.ts is already modified. Preserve it.
Do not read, copy or publish .env files, captured metadata or trained artifacts.

## 2. Product decision

**NetSentinel — understand your connection, know what to try next.**

Solve three user problems:

1. “Is this connection responding consistently right now?” Run a small,
   explicit browser HTTP check to this website and show the actual evidence.
2. “What should I try?” Provide symptom-specific, ordered, reversible steps for
   slow browsing, dropped video calls, disconnections and one failing website.
3. “How do I explain this to support?” Keep a small optional history on this
   device and export a plain text summary with method, time and limitations.

The result is a working public utility, not a landing page for the dissertation.
No account, payment, driver or backend is required for the public experience.

## 3. Feature decisions

| Decision | Feature | Reason |
| --- | --- | --- |
| Add | User-started, cancellable connection check | Provides useful real evidence immediately |
| Add | Response-time chart and success count | Makes short checks understandable without a technical score |
| Add | Guided troubleshooting with completed steps | Turns observations into practical next actions |
| Add | Bounded device-local history, comparison and deletion | Helps compare before/after a change without an account |
| Add | Downloadable support summary | Gives a visitor a useful artifact they control |
| Add | Transfer-time calculator from user-entered Mbps | Explains realistic waiting times without inventing speed measurements |
| Add | How it works, privacy and measurement limits | Explains the problem solved and how to use the product |
| Keep separately | Original local monitor at /local | Preserves working sensor, ML and research workflows |
| Remove from public journey | UUID entry, model scores, protocol tables, backend status | Unnecessary complexity for the chosen audience |
| Exclude | Automatic blocking, scanning, packet capture, AI chat, accounts, topology | Adds risk/complexity without solving this MVP's problem |
| Defer | True throughput tests and long-running outage monitoring | Needs calibrated endpoints, operating budget and wider validation |

## 4. Measurement contract

- Eight sequential fetches to one fixed same-origin, tiny JSON asset. Unique
  query values, browser cache disabled, per-request timeout of 3 seconds,
  bounded spacing, and one active check at a time. Cancel stops future probes.
- Validate the expected response; HTML from an intercepting portal is failure.
- Record elapsed HTTP response time using the monotonic performance clock.
  Report median, range and successful/failed HTTP requests. This includes browser,
  server and transport overhead; it is not ICMP ping, packet loss, bandwidth,
  router health, attack probability or a whole-internet diagnosis.
- A localhost/private-address deployment is LOCAL, not an internet test.
  Published-host checks are LIVE browser measurements, separate from sensor LIVE.
  Generated example results, if ever added, must be SIMULATION and isolated.
- Proposed advisory rule v1: failures prompt a retry and another-site comparison;
  median >= 300 ms prompts comparison, range >= 150 ms indicates variable
  responses. These are product heuristics, not validated service guarantees.
- A short successful check says only that this site answered the attempted
  requests. No “your internet is healthy” or security verdict.
- Hidden-tab cancellation prevents background scheduling from looking like
  connection degradation. Cancelled checks are not saved as complete results.

## 5. Architecture and public boundary

Reuse the existing frontend and locked dependencies. Build public components
with React and vanilla CSS, without a UI framework, remote fonts or copied repo.
Keep pure measurement/calculation/storage validation separate from presentation.

Prepare a second, allowlisted static build from only the public source files.
Publish that artifact with Sites. It contains no Django gateway, /local page,
sensor, .env, database, model, private inventory or session IDs. The original
Next application retains /local and its loopback-only relay for local use.
This boundary is enforced by build contents, not by hiding navigation.

Use fixed same-origin checks only: no URL input, public proxy or LAN probes.
No new database, account system, background worker or cloud sensor is needed.
Hosting receives ordinary HTTP connection metadata; the app does not submit
history or troubleshooting answers. Device storage can be disabled/unavailable;
checking and reports must still work. Keep at most 10 checks for 7 days, validate
loaded records, distinguish LOCAL/LIVE and provide clear deletion.

## 6. Delivery sequence and acceptance gates

1. Write this plan and designplan.md; record ADR-028 and contract updates.
2. Build the public overview, working check, chart and all result/failure states.
3. Add guided fixes, recent checks, export, calculator and how-to content.
4. Move the original dashboard entry to /local; preserve its contracts and tests.
5. Test arithmetic, partial/failed/invalid responses, cancellation, persisted
   input validation, retention and public/local boundary. Run existing frontend
   regression, lint, typecheck and a production build.
6. Inspect desktop/mobile UI, keyboard focus, wrapping and primary flows.
7. Generate the public static artifact using an explicit source allowlist;
   verify private API and local monitor are absent. Publish it to public users
   through Sites and record the successful deployment URL if available.
8. Update README, affected contracts and actual validation evidence. Do not
   equate a completed build with a successful public deployment.

## 7. Open-source approach

Reuse Next.js, React and the existing dependency lockfile; no external repository
is necessary for this focused product. Avoid adding a large dashboard template,
speed-test server or monitoring platform just because reuse is allowed. If a
future dependency is needed, verify its license, maintenance and actual purpose.
No new package is required for the first upgrade.

## 8. Research and limits

- MDN fetch cache behavior: https://developer.mozilla.org/en-US/docs/Web/API/Request/cache
- Microsoft consumer Wi-Fi troubleshooting: https://support.microsoft.com/en-us/windows/experience/connectivity-networking/fix-wi-fi-connection-issues-in-windows

These support cache configuration and general troubleshooting guidance; they do
not validate our thresholds or a user's hardware. Public release still depends
on available hosting authorization and a successful deployment. No new live
packet capture, ML accuracy or calibrated speed-test claim is part of this work.

## 9. Completion record

Implemented: the complete public helper, consumer design, working measurements,
guided fixes, history/comparison/deletion, export, planner and how-to/privacy view.
The original dashboard is retained at `/local`; public export excludes it and all
backend routes. Documentation and ADR-028 record the new contracts.

Validation: 37 frontend unit tests, 24 browser regressions and 93 offline sensor
tests passed. One real private-session smoke remains opt-in and unverified. Lint,
typecheck, normal production build and public export passed. Desktop/mobile and
real loopback HTTP checks were exercised. Publication and detailed limits are in
[PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).

Public launch completed: https://netsentinel-connect.hariharan4814.chatgpt.site
(hosting status `succeeded`; audience `public`).
