# NetSentinel Windows companion and public release execution plan

Updated 2026-10-02. This section is the active durable handoff. The earlier plan is
preserved verbatim below under Historical public-release plan. The current user
explicitly authorizes implementation, tests, dependencies, packaging and public
publication, superseding old documentation-only and excluded-feature decisions.

## Objective and approved scope

Deliver a useful MSc Computer Science project with two experiences: a public
connection/speed helper and an explicitly installed, authenticated Windows
companion for approximate application accounting, quotas, Windows security,
Defender scans, bounded connection history and private PDF reports. Preserve the
existing independent sensor, Django/PostgreSQL research system, Next/React app,
Isolation Forest semantics and LIVE/SIMULATION/REPLAY provenance. Never merge the
upgrade branch into main. Prepare reviewable commits and a draft PR if authorized
repository credentials are available. Public publication is authorized only for
the allowlisted static output; never publish the local stack or private data.

## Starting state and assessment

- Starting branch main; starting commit 59730913335567a48735895e02c2ff199876515f.
- Working tree was clean. Work branch: codex/windows-companion-release.
- Checkout C:/Users/yuvas/Desktop/NetSentinel; origin is the requested
  https://github.com/hariharan4814/NetSentinel-upgraded.git.
- Windows PowerShell host; Node v24.19.0; Git; existing frontend/node_modules and
  Python .venv, .venv-backend, .venv-ml directories. Python/gh not on PATH.
  Actual interpreter versions/dependency health still require fresh checks.
- Defender and NetSecurity cmdlets exist. Restricted shell denied CIM OS query;
  admin/capture rights, installed Npcap, live adapter visibility and Windows
  protection status are NOT yet verified. Driver installation/elevation is never
  automatic. PostgreSQL runtime availability remains unverified.
- Source inspected: public helper and optional bounded history, plain text export,
  troubleshooting, calculator, source-allowlisted static build; original /local
  dashboard and GET relay; modular Django metadata persistence/migrations;
  independent Scapy metadata normalization and Windows Npcap preflight; ML tools.
- Gaps: no companion package, authenticated local operator, per-executable bytes,
  quotas/firewall controls, Defender/scan UI, measured public throughput, provider
  lookup or proper PDF reporting. Historical test totals are not current evidence.
- Existing local Django and Next relay are loopback-only but unauthenticated.
  They need an authentication upgrade without elevating either web framework.
- No matching prepared patch/ZIP found in repository, tmp file listing or named
  NetSentinel/quota/companion files immediately in Desktop/Downloads. Implement
  equivalents; do not claim an earlier control upgrade exists in GitHub.
- Root AGENTS and README, architecture, product requirements, roadmap, security,
  modules, database/API, sensor, ML, design and test documents were inspected.
  Existing old sprint evidence remains historical, including conflicting totals.

## Architecture and security decisions

1. Keep public Next/React source and vanilla CSS. Extend its explicit static
   allowlist. Public pages never call loopback privileged APIs. The companion
   download/setup page explains the separate local experience and prerequisites.
2. Add modular Python companion packages independent of Django. A loopback-only
   authenticated local service serves its own local dashboard and bounded JSON
   API. A separate explicitly started privileged broker exposes only fixed,
   authenticated actions for owned firewall rules and Defender scans. Never accept
   arbitrary commands, script text or executable paths from browser requests.
3. Use SQLite for companion-only durable settings/accounting/control history,
   schema versioning and transactions; preserve existing PostgreSQL research
   models/migrations. No mandatory Redis/Celery or background cloud service.
4. Approximate packet-to-socket snapshot attribution, grouped by canonical
   executable identity. Unique match only; ambiguous/missing traffic unassigned.
   Count observed IP bytes, never interface bytes as app bytes, never ISP billing.
   Explicit capture permission/interface; known missing capture is unavailable.
5. Local credentials, exact Host/Origin validation and mutation protection. The
   broker accepts observed executable IDs resolved from trusted local state,
   protects OS/companion components, owns a fixed firewall rule group, and has
   explicit cleanup/recovery. Applied rule is not proof of traffic blocking.
6. UTC observations and reset boundaries initially UTC, clearly labelled. Daily
   and monthly quota states, warning percentage, opt-in enforcement, reset-scoped
   override and bounded event history survive restart. No anomaly-driven block.
7. Fixed documented Windows interfaces for status/scans. No fabricated score,
   progress percent or unavailable results. Defender performs remediation.
8. External public speed/IP services require primary-source terms/license/CORS
   review before selection. Explicit user initiation, bounded transfer/time,
   cancellation, actual application-byte counts and clear endpoint/method limits.
9. Browser and companion PDF exports use maintained libraries after license
   review. Sensitive addresses/paths/location default hidden. Public scope never
   invents local data. Report date ranges reflect retained observations only.

## Ordered work, requirements and acceptance gates

| ID | State | Task and acceptance criteria |
|---|---|---|
| P0 | VERIFIED | Inspect and save this plan before implementation; dedicated branch; preserve previous plan. |
| P1 | IN_PROGRESS | Application discovery and attribution: tested ambiguity, stale snapshots, wildcard sockets, same-executable subprocess grouping; unmatched bytes and coverage shown. |
| P2 | IN_PROGRESS | Persistent daily/monthly quotas, thresholds, reset time, override, observation/enforcement modes, bounded action history; tests for edges, restarts and failed firewall actions. |
| P3 | IN_PROGRESS | Narrow broker, owned firewall block/unblock/cleanup, protected components, authenticated loopback API; hostile Origin/Host, invalid IDs/inputs and crash-recovery tests. |
| P4 | IMPLEMENTED | Defender/passive/unavailable and all three firewall profiles, signature/scan age; real documented status with failures presented. |
| P5 | IMPLEMENTED | Explicit Quick/Full scan controls, bounded jobs and real state/results; permission/missing/passive/long-running cases tested; no invented progress. |
| P6 | IN_PROGRESS | Bounded observed-flow metadata/usage and evidence-based outbound/burst/new-destination alerts; provenance, retention and baseline gaps tested; keep existing model separate and unchanged. |
| P7 | IN_PROGRESS | Public measured download/upload/latency/jitter, consent/cancel/stages/bytes/history/comparison; engine/endpoint license/terms documented; failure/math tests. |
| P8 | NOT_STARTED | Explicit visitor-side public IP/ASN/provider/approximate location lookup with source/failures/redaction; companion local adapter details. |
| P9 | NOT_STARTED | Proper public/local selected-section PDFs and date ranges, tables/charts/privacy controls; generate labelled non-private examples and inspect rendered pages. |
| P10 | IN_PROGRESS | Integrated responsive accessible UI, local research auth, regression/security checks, lint/typecheck, production/static builds and public artifact exclusion checks. |
| P11 | NOT_STARTED | Windows package install/start/stop/uninstall, version, prerequisites, owned-rule recovery, unsigned disclosure and update strategy; controlled actual attribution/blocking/overshoot/resource evidence. |
| P12 | NOT_STARTED | Publish approved public artifact to existing Site; verify URL and primary flows; commits/draft PR if access; docs/contracts/final-year demo and final handoff. |
| D1 | DEFERRED | Access schedules, malicious-destination feeds, custom antivirus/quarantine, throttling, remote-device guarantees and unvalidated model transfer. |

Implemented means code exists. VERIFIED requires recorded passing evidence for
that scope; unit fixtures never prove actual Windows networking or deployment.
A module may be implemented while its hardware/release gate remains BLOCKED.

## Dependencies, database and deployment

Existing lockfiles remain authoritative. Existing pinned Python packages include
psutil 7.2.2 and Scapy 2.7.0; Next 16.3.5 / React 19.3.0 / TypeScript 5.9.3.
New dependency selection and version/license verification are outstanding. Prefer
focused MIT/BSD/Apache components; do not redistribute Npcap without appropriate
license. Document selected PDF/speed/packaging dependencies in this section after
primary-source research; preserve notices and reproducible locks.

No PostgreSQL schema change is currently planned; run migration consistency and
existing test suite. Companion SQLite schema v1 is separate local-only state,
with bounded retention and backup-before-upgrade instructions. Do not copy the
research database/private traffic/model artifacts into distributions.

Existing Site project appgprj_6abe7cb737b48191aecdf0a81f9caf4e and public URL
https://netsentinel-connect.hariharan4814.chatgpt.site must be reused. Static build
stages only explicit public source files and excludes /local, API, companion,
sensor, env and private data. Current hosting helpers/tool availability, source
push credentials and publishing permissions must be checked at release time.
No signing key is available in this session; default package is UNSIGNED. Do not
claim Windows SmartScreen acceptance. Release download must identify version,
SHA-256 and prerequisites, and link to an actual produced artifact.

## Test commands and Windows verification procedure

Fresh baseline and follow-up checks (use actual installed interpreters):
- frontend: npm test; npm run lint; npm run typecheck; npm run build;
  npm run test:e2e; npm run build:public (review/remove only generated staging).
- sensor: .venv/Scripts/python.exe -m unittest discover -s tests.
- backend: .venv-backend/Scripts/python.exe backend/manage.py test --settings=config.test_settings;
  normal-settings check and makemigrations --check --dry-run when configured.
- companion: proposed python -m unittest discover -s companion/tests; record
  exact final invocation and tests/counts after implementation.
- git diff --check; inspect package/static file allowlists and credentials bounds.

Windows manual gate: explicitly choose a non-loopback interface and consent to
capture; use a controlled disposable executable for bidirectional traffic;
compare captured metadata and attributed IP bytes, including unassigned traffic;
measure capture gaps/CPU/working set and socket-snapshot ambiguity. Set a small
quota only on that controlled executable; measure quota overshoot in bytes/time;
verify a new connection fails after rule application and succeeds after unblock.
Test reset and override with a fake clock in unit tests, never change OS time.
Stop normally and verify owned rules removed; interrupt/kill only our agent,
restart/reconcile and verify cleanup; verify unrelated firewall rules unchanged.
Run read-only actual Defender/firewall queries, then an explicitly user-started
Quick scan if permissions permit. A Full scan remains a UI/manual verification
procedure unless separately chosen; never start one silently. Do not download
malware for demonstration. Document unavailable/passive results faithfully.

PDF QA: non-private SIMULATION fixtures, long executable labels, multiple pages,
redaction defaults/opt-ins, date ranges, unavailable sections, meaningful chart
labels, browser/mobile downloads, render and inspect sample pages.

## Risks and unresolved gates

- Restricted process cannot currently query CIM; privileges/capture and native
  driver availability need measured verification, with no silent elevation.
- Packet/socket correlation is approximate and can miss short-lived, shared UDP,
  fragmented, offloaded or inaccessible-process traffic; expose unassigned bytes.
- Reliable firewall crash recovery needs persistent owned-rule reconciliation;
  enforcement is opt-in and can interrupt applications. Critical apps protected.
- External speed service terms/CORS/rate and bandwidth caps need research; if no
  permitted endpoint is available, implement configured endpoints and mark live
  throughput verification BLOCKED rather than using invented readings.
- Defender may be passive/missing; status query success is not a safety verdict.
- No signing credentials, GitHub CLI currently absent from PATH; publishing/PR
  access and public binary hosting remain to verify.
- Previous generated public-release files and tmp contain private historical
  datasets; never read/copy them into reports or packages. Use fresh labelled
  non-private fixtures only. Preserve old migration and model contracts.

## Milestone log

2026-10-02 assessment: clean main at 5973091; inspected required documentation and
actual public/sensor/backend source. No implementation changes/dependency installs,
migrations, scans, firewall mutations or deployment performed yet. Restricted Git
branch creation failed due .git permissions; retry with scoped authorized access.
CIM read denied; source and local cmdlet discovery still possible. No fresh tests.

### Resumption checkpoint - 2026-10-02

User requested resume after agent usage-limit interruption. Branch verified as
codex/windows-companion-release; HEAD still 59730913335567a48735895e02c2ff199876515f.
Saved plan preceded all code/dependency changes. Partial files present:
companion/{identity,attribution,store,windows_security}.py; Next local-auth
route/library/login component; Django auth middleware/settings; frontend lockfile
adds @cloudflare/speedtest 1.14.1, jspdf 4.2.1 and jspdf-autotable 5.0.8. These
are unfinished and unverified. No new source commit, scan, firewall mutation,
migration, package or deployment. Existing public release remains unchanged.

Scoped runtime inspection succeeded using authorized host execution: Python
3.11.0, psutil 7.2.2, Scapy 2.7.0, Windows build 10.0.26300. Defender reported
Normal, antivirus and real-time protection enabled; this is read-only evidence,
not a safety verdict. Standard C:/Windows/System32/Npcap/wpcap.dll absent, so
packet capture/real attribution gate is BLOCKED pending explicit driver setup.
No Npcap is bundled (official redistribution license requires authorization).
ReportLab/PyInstaller absent from project .venv. Restricted Python launcher fails;
use scoped authorized execution for existing interpreter and tests. No fresh
automated tests have run yet. Agents resumed on disjoint files; root owns plan.

Immediate next action: add attribution/quota persistence tests and finish native
collector, narrow broker and local companion API/UI; run companion tests before
claiming implementation verification. Review agent results rather than assume
completion. Prior Resume instructions below remain applicable where unfinished.

### Implementation checkpoint - resumed 2026-10-02

Root added companion attribution, SQLite quotas/usage/flow events, bounded
loopback HTTP boundary, optional privileged broker, collector and vanilla-CSS
local dashboard. Windows adapters and their tests/docs completed by agent.
Local-auth agent added Django scoped bearer authorization, Next operator session
login/CSRF, ML publication env keys and test fixtures/docs. Public agent added
speed/IP/PDF modules and UI plus public-source allowlist; its final QA/docs are
still pending. Branch and HEAD remain codex/windows-companion-release / 5973091;
all new code is currently uncommitted. No live scans/rules/capture/deployment.

Evidence: first 11 attribution/accounting tests passed. Agent-reported focused
Windows adapter tests: 31 passed including 5 memory-only PowerShell fixtures;
read-only actual Defender active and all 3 firewall profiles enabled; owned-rule
query returned zero rules/conflicts. Local-auth agent reported backend56,
frontend43 and ML-publication3 passed, migration dry-run no changes. Those counts
predate later public additions and need combined regression before release.
Root companion56 run found 2 wildcard address-family failures, with5 optional
PowerShell fixtures skipped; both were corrected immediately, recheck pending.
Root also fixed 2 independently reproduced broker disconnect/restart bugs by
reconciling observed owned rules instead of stale in-memory applied flags; those
2 regression tests now pass. No claim of actual traffic-blocking verification.

Dependencies: ReportLab5.0.1 (BSD) installed in .venv with Pillow12.3.0 and
charset-normalizer3.5.2 for proper local PDF reporting (reports module pending).
Primary license sources: https://docs.reportlab.com/developerfaqs/ and
https://pypi.org/project/reportlab/. Npcap absent and not redistributable under
its ordinary free license; manual prerequisite only. Scapy is GPLv2; distribute
our source installer with notices and separate user installation of dependencies,
never bundle Npcap or unreviewed third-party binaries. Public agent patched
Next/eslint-config-next to16.3.8 after advisory review; preserve updated lockfile.

Resume next: finish local PDF module, CLI/private-state provisioning and Windows
source installer; rerun all companion tests, then combined public/auth frontend
QA, schema checks, safe package build and real read-only UI checks. Live capture
remains blocked by missing Npcap; do not install it silently. Record separate
packaging/deployment blockers. No new long-running process started yet.

## Resume Here

1. Confirm active branch is codex/windows-companion-release and this plan is saved.
2. Update P0 to VERIFIED once confirmed; research primary Windows interfaces and
   PDF/speed dependencies. Inspect actual interpreter/Npcap/backend availability.
3. Implement P1-P3 first; delegate disjoint Windows status/scan and public speed/IP
   components if useful, with root as sole plan.md owner. Every agent reports files,
   tests, gaps and next steps for inclusion here.
4. Continue ordered gates, writing milestone evidence here after each meaningful
   increment. Keep future work NOT_STARTED; never reuse historical test totals.
5. Existing ignored public-release/dist and frontend/.public-build may remain
   from previous release; inspect before rebuilding. Prior local servers may own
   ports 3210/3211; identify our process before stopping any process. No new process
   has been started for this upgrade. Preserve generated release assets until
   replacements are tested. Latest relevant commit remains starting commit above.

---

# Historical public-release plan (preserved; 2026-10-01)

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
