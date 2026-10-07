# NetSentinel handoff to Google Antigravity

## Current checkpoint — 2026-10-07

**The local AI prototype is complete; stop core coding.** Read the current
[plan.md](plan.md) Resume Here before the historical entries below. Core source
is committed on `codex/ai-lab-prototype` (`c233830`, `9a3d1ae`); final documentation
and release housekeeping follow. Preserve the unrelated next-env.d.ts edit.

The project now generates virtual metadata, trains/evaluates real IF/RF models,
compares baselines, explains with validated SHAP, runs repeated-seed/unknown-family
studies, and offers an authenticated glass UI with playback and PDF/JSON export.
Everything is explicitly SIMULATION. No packets or attacks are emitted.

Setup and viva: [AI_LAB_SETUP.md](docs/AI_LAB_SETUP.md). Start with
`.venv-lab/Scripts/python.exe scripts/run_ai_lab.py` from the repository root.
The separate SQLite lab runtime needs no PostgreSQL/Npcap/admin. Existing research
PostgreSQL and Windows companion are preserved, with their limitations unchanged.

Verified: lab 41, backend 70, frontend 58 tests; 31 browser passes/1 opt-in LIVE
skip; build/lint/types/public exclusion; actual browser training and mobile PDF
download; final ten-page semantic report individually rendered/inspected. Earlier
sensor/ML/companion regressions passed with explicit skips recorded in plan.md.
Actual auth/cancellation/full-stack restart integration passed after final fixes.
All QA servers/workers have been stopped. Generated evidence paths and hashes,
source commit details, tested commands and exact remaining procedures are in plan.md.

Remaining work is outside the verified core: PostgreSQL installation/integration
BLOCKED; external dataset access BLOCKED; optional LLM/public AI showcase,
drift/ablation and production Windows release/signing DEFERRED. Do not fabricate
completion or re-run old capture/control actions to make the AI demo look LIVE.
Source release/PR status is recorded in the final release checkpoint in plan.md.

## Historical handoff entries

## Earlier checkpoint — resources downloaded; coding later

The user's latest instruction is to download external resources first and leave
application coding for later. R0 core acquisition is complete: **40 inventoried
artifacts / about 129 MB**, including 20 candidate wheels, two source archives,
three papers, licenses/docs and the optional Qwen model reference. Read the
[resource guide](resources/ai-lab/README.md),
[inventory](resources/ai-lab/manifest.json) and current [plan](plan.md).

Publisher hashes, archive integrity and offline hash-required resolution passed;
installed packages were unchanged. Nothing was installed/trained and no product
code changed. Python 3.11.0/pip 22.3 work with scoped permission outside the
restricted sandbox; do not rebuild environments because of earlier launcher
errors. SHAP 0.51.0 is cached for Python 3.11; runtime/Numba integration and
explanation correctness still require tests in the future coding phase.

CICIDS2017 CSV is **BLOCKED** at official registration; no identity was submitted
or mirror substituted. Optional LLM weights/runtime are **DEFERRED**. Neither
blocks the independent simulator. A1–A8 remain NOT_STARTED. Next coding action
is A1's contracts/schemas/split protocol.

The cache is ignored by Git: preserve it separately during handoff or re-fetch
using manifest URLs/hashes. Branch/commit unchanged:
`codex/windows-companion-release` / `65966ed`. No background process remains.

## New active task — AI Lab prototype plan, 2026-10-04

**Read the new top section of [plan.md](plan.md) first.** The user has redirected
the project toward an M.Sc. AI prototype: generated benign/attack-like traffic,
real model training, explainable predictions, comparisons and a reproducible
demonstration. They asked for a clear plan before proceeding. The initial
checkpoint was documentation only; no AI Lab implementation or experiment result
is claimed. The old release handoff below is preserved for reference.

Current branch: `codex/windows-companion-release`. Starting/latest relevant
commit: `65966edfd73f85370ed0ee65baa78a11b1a1d50d`. Preserve the existing
`frontend/next-env.d.ts` modification and all newer work. Check Git status rather
than assuming the tree is clean. Do not reset to the old handoff's starting commit.

### What the next agent should build

1. A seeded, bounded metadata simulator using existing sensor aggregation; it
   sends no packets and needs no administrator rights or Npcap.
2. A genuine ML experiment pipeline: Isolation Forest, Random Forest behaviour
   classification, rule/dummy baselines, disjoint run-group splits and honest
   held-out evaluation. Never confuse synthetic labels with real attack proof.
3. An authenticated local `/lab` with Scenario Studio, Training, Detection,
   Explain & Compare, and research reports. Use the revised `designplan.md`.
4. Learned-reference and SHAP explanations, reproducible JSON/PDF results and
   a viva guide including false positives and limitations.
5. Optional extensions after the core: local grounded AI assistant, separate
   CICIDS2017 benchmark and a labelled recorded public simulation showcase.

### Exact starting work and caveats

- Start **A1 in `plan.md`**: finalize the lab contracts, features, labels and
  grouped split protocol. Then implement the A2/A3 CLI vertical slice before UI.
- Existing `ml/pipeline.py` slices rows into 180/60/60 and does not enforce
  independent run groups across those splits. An old test name/docs claim more
  than the implementation proves. Do not reuse that as a verified lab split.
- Existing `backend/detection/explain.py` defaults to static reference numbers.
  A new lab explanation needs statistics from its saved training data/model.
- Root `unittest discover -s tests` is the publication-auth suite, not all sensor
  tests. Run `tests/sensor` and `tests/ml` explicitly; exact commands are in the
  active plan. Historical totals below are not current lab evidence.
- Current source uses `ipwho.is` for lookup and `NETSENTINEL_*` auth variables;
  reconcile active documentation drift during A1 instead of copying old summaries.
- Preserve host-v1, original model compatibility, provenance and the independent
  sensor. Give new lab models their own bundle contract. No automatic LIVE
  promotion, anomaly-driven firewall blocking or fake training progress.
- Proposed new `lab` commands, Django experiment app and worker do not exist yet.
  No new dependency, model weights, migration, synthetic dataset or running job
  was created during this planning checkpoint.
- Planning-document checks passed using PowerShell. A `.venv` Python launcher
  failed to start its referenced interpreter; diagnose runtime availability before
  tests rather than assuming old environment versions still work. This was not
  an application-test failure, and the cause is not established.
- Old Windows privileged-install/blocking/signing gates are **deferred for the
  AI core**; they still apply before a production companion release. The public
  site has not been updated with AI Lab features. Do not claim otherwise.

The active plan has ordered tasks/states, licenses and references, database/API
design, validation commands, risks and a durable **Resume Here** section. Record
each implementation milestone there, with exact results and current commit.
Keep this file as a concise entry point rather than a competing status ledger.

---

## Historical Windows companion release handoff (2026-10-02)

Handoff requested by the user on **2026-10-02 (Asia/Calcutta)**. The user asked
Codex to stop the larger upgrade, stabilize work in progress, and leave exact
continuation instructions. **This is not a completed release.** Do not interpret
the old research sprint completion claims as acceptance of this upgrade.

## Start here

1. Work in `C:\Users\yuvas\Desktop\NetSentinel`.
2. Read `AGENTS.md`, the active top section of `plan.md`, this file, and current
   Git status. The user explicitly authorized implementation, overriding old
   Sprint 0 documentation-only restrictions. Privacy/scientific rules still apply.
3. Branch: `codex/windows-companion-release`. Starting commit:
   `59730913335567a48735895e02c2ff199876515f` (`main` at task start).
   Run `git branch --show-current`, `git log -3 --oneline`, and `git status --short`
   for the final checkpoint. Preserve all current work; do not reset to main.
4. Use the state vocabulary `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`,
   `VERIFIED`, `BLOCKED`, `DEFERRED`. A passing mock is not hardware verification.
5. Finish the remaining checks and release gates below. No merge to main was
   authorized. A draft PR and public deployment were authorized in the earlier
   implementation task, but neither has been completed for this upgrade.

## Intended product and boundaries

Public website: retain the existing HTTP connection helper, add explicit measured
speed testing, visitor-side optional network lookup, bounded local history and
semantic PDF reports, plus a genuine companion release link when available.

Installed Windows companion: approximate executable traffic accounting, daily
and monthly quotas, opt-in firewall enforcement, actual Defender/firewall status,
explicit Defender scan controls, bounded observed-flow metadata, explanations and
private PDFs. Keep the existing independent sensor and Django/PostgreSQL/ML
research monitor intact. Never claim an anomaly is an attack or malware probability.

Public static export is source-allowlisted. Never publish the normal Next server,
`/local`, APIs, companion source, `.env`, databases, packet records, historical
private inventories or models as website assets. The companion download should
be a separately verified GitHub release asset. Public pages never call loopback.

Local Next/Django stay unprivileged and loopback-bound. The companion's normal
Python dashboard is also loopback-bound and authenticated. Its optional broker
accepts a separate secret, rejects browser Origins, resolves executable IDs from
its own observed processes, and exposes only fixed native operations. No browser
path or arbitrary PowerShell command is accepted. Never reset the whole firewall.

## Current source inventory

| Area | Current state and ownership |
|---|---|
| Planning | `plan.md` saved before all application/dependency changes; previous public release plan preserved beneath current plan. |
| Attribution / quotas | `companion/identity.py`, `attribution.py`, `store.py`: canonical SHA-256 executable IDs; grouped subprocesses; ambiguous/stale/fragmented traffic unassigned; SQLite v1 UTC daily buckets, quotas, warnings, resets, overrides, persistent manual intent, bounded history. |
| Capture | `companion/collector.py` reuses existing Scapy normalizer/preflight; explicit adapter and consent; metadata-only bounded queue; socket refresh; link/address-change failure; no packet storage. Needs actual integration validation. |
| Native adapters | `companion/windows_security.py`, `firewall.py`: fixed native scripts, bounded runner, sanitized status/errors, all profiles, available scans/detections, owned inbound/outbound rules, rollback and cleanup. |
| Local service | `companion/http_boundary.py`, `broker.py`, `service.py`, `__main__.py`: authenticated bounded loopback API, separate broker, owned-rule reconciliation, watchdog, CLI lifecycle, private token initialization. Integrated install/security review is unfinished. |
| Companion UI | `companion/web/{index.html,style.css,app.js}`: vanilla glass UI with overview, apps/quotas, Windows status/scans, flows/alerts, PDF reports and guide. Not yet browser-tested as an installed application. |
| Companion PDFs | `companion/reports.py`: semantic tables/vector chart, pagination, selected sections/date range, paths/IPs hidden by default. Sample in `docs/examples/companion-report-simulation.pdf`; generator fixture in tests. |
| Research authentication | Django scoped read/ingest/model bearer tokens; Next HttpOnly session/CSRF login at `/local`; ML publisher env keys. See `docs/LOCAL_AUTH.md`. Existing real env files were NOT changed. |
| Public tools | `frontend/src/lib/public-measurements.ts`, `public-report.ts`, `components/public/public-tools.tsx`, existing public app/CSS and build allowlist extended. See `docs/PUBLIC_MEASUREMENTS.md`. |
| Dependency updates | Next/eslint-config-next patched16.3.8; Cloudflare speedtest1.14.1, jsPDF4.2.1, AutoTable5.0.8 pinned in npm lock. Python companion requirements pinned separately. |
| Packaging | `companion/packaging/*.ps1` and `scripts/build_companion_release.py` are a source-installer WIP. Treat it as an unsigned developer preview, not a verified installer or privileged production release. |

## Environment and known facts

- Windows build10.0.26300; host execution is **not an elevated Windows admin
  token**, even when Codex tools use `require_escalated`. That tool bypasses the
  workspace sandbox; it is not UAC elevation.
- Node24.19.0, Python3.11.0 at `.venv/Scripts/python.exe`; separate existing
  `.venv-backend` and `.venv-ml` remain. Python/gh were absent from ordinary PATH.
- Restricted Python and tsx launches sometimes failed. Authorized host execution
  worked. Do not misclassify sandbox launcher errors as application failures.
- **Npcap was initially absent. The user installed it explicitly.** Afterwards,
  `capture_preflight()` passed, `npcap` service was Running, and `Ethernet 3` was
  the only eligible adapter name reported. This is driver/preflight evidence,
  not packet attribution verification. Do not reinstall the driver blindly.
- Actual read-only adapter calls reported Defender Normal/active, antivirus and
  real-time protection enabled, all three firewall profiles enabled, and zero
  NetSentinel-owned rules/conflicts. No protection was changed, no scan started.
- Git credential helper is `manager`; GitHub CLI not found. Repository access
  for push/release/PR has not been proven. Do not print credentials from helper
  output. Use normal credential tooling, with secrets only in process memory.
- Existing public Site is
  `https://netsentinel-connect.hariharan4814.chatgpt.site`, project ID
  `appgprj_6abe7cb737b48191aecdf0a81f9caf4e`, audience public. It still serves the
  **previous** published version; this upgrade has not been deployed.
- `frontend/public/companion-release.json` intentionally has `available:false`.
  Never turn it on until a real asset URL, version and checksum are verified.
- Ignored `tmp/` contains older private research data. Do not use it as a source
  for examples, commits, ZIPs or public assets. New examples are SIMULATION.

## Important bugs already found and corrected

1. Broker disconnect/restart could leave a real block in place after UI unblock,
   or skip reapplying an intended block after recovery. `Companion.reconcile()`
   now queries actual owned rules and accounts for both directions. Both focused
   regressions passed after the fix. It never claims verified traffic blocking.
2. Wildcard UDP owners initially matched across IPv4/IPv6 families. Matching is
   now address-family conservative; edge regressions pass.
3. A native PowerShell rule-name array construction bug was found with memory-only
   execution of the real script and fixed before any live firewall mutation.
4. PDF privacy test initially looked for mixed-case paths after canonicalization;
   assertion now checks normalized text. Default and opt-in redaction tests pass.
5. Missing attributed observations now carry `observed:false`; UI renders them as
   unavailable observations rather than claiming zero per-application usage.

## Remaining work, in order

### 1. Finish integrated companion review and tests — IN_PROGRESS

- Run all companion tests including opt-in memory-only native fixtures. No fixture
  modifies real rules. Add integration tests for actual HTTP authentication,
  report downloads, shutdown and CLI provisioning.
- Review service/broker concurrency, timeout consistency, cleanup errors, thread
  termination and restart reconciliation. Native rule calls can take seconds;
  measure quota overshoot rather than claim instantaneous enforcement.
- Review private-state ACL handling: current `init` removes inherited permissions
  and grants user/SYSTEM/Administrators, but pre-existing explicit ACL grants and
  reparse points need hardened handling before a public privileged release.
- **Privileged install boundary is unfinished.** Current source scripts would
  launch a broker from a user-writable per-user Python/source install. Before a
  general release, put broker code/runtime/dependencies in an administrator-owned
  location with protected ACLs and a reviewed launch path (e.g. a separately
  installed Program Files broker). Do not imply that an HTTP allowlist alone
  protects mutable elevated Python code. Normal dashboard remains unprivileged.
- Validate timestamp/report-range intersections and retained-data limitations;
  add negative/future/outside-retention tests. Current daily aggregation cannot
  produce sub-day billing-grade reports, and that is not a supported claim.
- Quota modes and manual intent persist. Exiting/recovery removes rules, but
  re-enabling a persisted policy can reapply it; document/test expected startup
  behavior and warn clearly when cleanup cannot be confirmed.
- Source-only packages should retain relevant notices. Npcap is separately
  installed and must not be redistributed without its appropriate license.

### 2. Real Windows verification — IN_PROGRESS / privileged portion BLOCKED

- User has installed Npcap; rerun its preflight, do a short controlled capture
  on `Ethernet 3` with explicit `--consent`, and compare packet IP-byte reference
  to unique executable attribution. Use `scripts/verify_windows_capture.py` only
  if it exists and has been reviewed/completed. Do not assume an interrupted
  agent ran it. Preserve unassigned bytes and short-lived-connection gaps.
- Use only controlled traffic, filter to its fresh tuple, and save aggregate
  counts/resource evidence, not real addresses, paths, payloads or inventories.
- Actual block/unblock, quota overshoot, cleanup on normal shutdown, broker lease
  expiry, broker crash recovery, unrelated-rule preservation and uninstall recovery
  require an explicitly elevated native test. The current host token is not admin.
  Never silently elevate, change OS time, alter existing security settings or
  block system/companion executables. Never equate a rule with tested blocking.
- Actual Quick scan integration remains unverified. Full scan is user-start only;
  do not launch it simply to manufacture a test result. Defender owns remediation.

### 3. Frontend production/browser regression — IN_PROGRESS

- Unit/lint/type checks passed during agents' work; rerun against final source.
- A production `npm run build` was started before the stop request. Inspect its
  completion record below and `.next` before running browser tests.
- Run `npm run test:e2e`. Local-auth browser fixtures contain clearly labelled
  test-only credentials; they are not runtime secrets. Existing private-session
  real-data smoke is opt-in, not an expected default pass.
- Browser QA desktop/mobile: public HTTP check; speed consent/cancel/error and
  measured result; history retention/deletion; lookup consent/disable/error;
  PDF selection/redaction/download; local sign-in/logout; companion auth,
  quota forms, missing-driver/permission states, security queries and downloads.
- Test live Cloudflare CORS/throughput once (nominal15.5MB payload, worst retry
  attempt budget62MB). Test user-side IP lookup without logging/screenshotting
  personal IP/location. Fixture success is not a live-service check.

### 4. Complete packaging and release gates — IN_PROGRESS

- Finish/check `docs/COMPANION_SETUP.md`, `COMPANION_UPGRADE.md`, hashed Windows
  wheel lock and `companion/THIRD_PARTY_NOTICES.txt` required by package builder.
- Build an allowlisted source ZIP with `scripts/build_companion_release.py`.
  No `.env`, `.token`, SQLite, packet data, models, virtualenv or Npcap in ZIP.
  Keep version0.2.0 and publish its actual SHA-256. Scripts/build are UNSIGNED.
- Test clean install and safe upgrade/uninstall in an isolated Windows account
  or VM. Do not run uninstall against this source checkout. Installer must not
  overwrite an existing install or remove unrelated files/rules. Prepare protected
  broker installation before claiming privileged distribution is ready.
- No source/binary package is signed; no signing key was available. Document
  manual verified updates and future Authenticode/update-signing strategy.
- Create clear commits/draft PR if access permits. Do not merge main.
- Publish companion release asset only when accurate release gates/limitations
  are documented. Update `companion-release.json` only after verifying that URL.

### 5. Public export and deploy — NOT_STARTED for this upgrade

- Build `npm run build:public` from the explicit allowlist. Existing generated
  `.public-build` and `public-release/dist` must be inspected and removed only
  after resolving their absolute paths under this checkout. Keep the Site manifest
  and release Git history; never recursively remove the whole public-release repo.
- Verify no local route/API/source/secret enters export. Test artifact independently.
- Use the existing Site project/audience; do not create a new site. Hosting skill
  path available at the last check:
  `C:/Users/yuvas/.codex/plugins/cache/openai-curated-remote/sites/0.1.75/skills/sites-hosting/SKILL.md`.
  Its `scripts/site-workflow.mjs` was present at the last check. Credentials stay
  in session memory/hidden stdin, never plan/docs/arguments/files.
- Native Sites workflow requires source commit push, archive save, deploy, and
  a `succeeded` deployment with URL. Then verify primary deployed flows as the user
  requested. If unavailable, mark deployment BLOCKED and retain release artifact.

### 6. Documentation integration — IN_PROGRESS

- Update root README, designplan.md, architecture ADR register, API/database/
  security/module/product/test/roadmap documents to describe the final source.
  Agent docs already contain detailed public/auth/Windows interface contracts;
  root cross-document reconciliation is still pending. Preserve historical evidence
  but make its scope obvious. Do not let old unauthenticated statements override
  the new implemented auth boundary.
- Add final-year demo instructions: public check/speed/report; local observed apps
  and quota warnings; security status; explicitly controlled block/scan only if
  supported; separate deterministic SIMULATION; model caveats and coverage.
- Keep `plan.md` and this handoff accurate. Do not mark hardware/release verified
  because mock tests passed. Deferred: schedules, threat feeds, custom antivirus,
  throttling, unvalidated remote-device claims/model transfer.

## Exact commands

PowerShell, repository root unless `Push-Location` says otherwise:

```powershell
git status --short
git branch --show-current
.\.venv\Scripts\python.exe -m companion version
$env:NETSENTINEL_POWERSHELL_FIXTURE = '1'
.\.venv\Scripts\python.exe -m unittest discover -s companion/tests -v
Remove-Item Env:NETSENTINEL_POWERSHELL_FIXTURE
.\.venv\Scripts\python.exe -m unittest discover -s tests
Push-Location backend
..\.venv-backend\Scripts\python.exe manage.py test tests --settings=config.test_settings
..\.venv-backend\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
Pop-Location
Push-Location frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
npm run test:e2e
npm audit
Pop-Location
git diff --check
```

Backend tests must run **from backend cwd** with `tests`; running the wrong discovery
from the root previously found zero tests. Do not record zero tests as a pass.
`pypdf6.19.0` is installed only for companion PDF QA, not runtime requirements.
`reportlab5.0.1`, Pillow12.3.0 and charset-normalizer3.5.2 were installed into .venv.
The ignored `tmp/companion-wheels` contains the five pinned official wheels used
to prepare Windows Python3.11 x64 hash locking. Keep these out of source/public ZIP.

## Final validation and process checkpoint

Completed by Google Antigravity on **2026-10-02**:

### 1. Test & Build Execution Results
- **Companion Test Suite**: `.\.venv\Scripts\python.exe -m unittest discover -s companion/tests -v`
  - Result: **58 / 58 PASS** (7.25s). Includes accounting, attribution, address family edge cases, loopback boundary, controls, firewall mock/PowerShell fixtures, semantic PDF generation, native runner, and Defender status.
- **Sensor Test Suite**: `.\.venv\Scripts\python.exe -m unittest discover -s tests`
  - Result: **3 / 3 PASS** (0.005s).
- **Backend Test Suite**: `..\.venv-backend\Scripts\python.exe manage.py test tests --settings=config.test_settings` (executed from `backend/` cwd)
  - Result: **56 / 56 PASS** (0.76s).
  - Migration check: `makemigrations --check --dry-run` reported **No changes detected**.
- **Frontend Test Suite**:
  - `npm test`: **52 / 52 PASS** (0.64s).
  - `npm run lint`: **0 warnings** (Clean).
  - `npm run typecheck`: **0 errors** (Clean).
  - `npm run build`: **Next.js 16.3.8 production build succeeded**.
  - `npm run test:e2e`: **29 passed, 1 skipped** (30.1s; Playwright E2E browser tests).
- **Public Static Export**: `npm run build:public`
  - Result: **SUCCESS**. Verified static export to `public-release/dist`. Forbidden assets (`api`, `local`, `.env`, `backend`, `sensor`) checked and confirmed absent.
- **Companion Source Package**: `python scripts/build_companion_release.py`
  - Result: **SUCCESS**. Generated `output/releases/NetSentinel-Companion-0.2.0.zip` (94,468 bytes, 36 allowlisted files; SHA-256: `20cb3bc6bc35c4b65458b1578e1566f091d27931d1cb25d4e251b8b3336e4eb4`).
- **Npcap Driver & Preflight**:
  - `capture_preflight()` and `capture_interfaces()` executed and succeeded; enumerated adapters (`Ethernet 3`, `Wi-Fi`, `Loopback`, etc.).
- **Code & Tree Formatting**:
  - `git diff --check`: Clean (0 whitespace/formatting issues).

### 2. Documentation & ADR Reconciliation
- `ARCHITECTURE.md`: Registered ADR-028 through ADR-033 covering public static boundaries, companion SQLite v1, narrow privileged security broker, authenticated local stack, privacy-first PDF generation, and unsigned source package distribution.
- `API_PLAN.md`: Reconciled public Cloudflare measurements, upgraded Django scoped bearer auth, Next.js session/CSRF authentication, Companion loopback API (port 8765), and Privileged Broker API (port 8766).
- `DATABASE_PLAN.md`: Documented Companion SQLite v1 schema (`PRAGMA user_version=1`, `executables`, `daily_usage`, `policies`, `flow_events`, `settings`) and verified total isolation from research PostgreSQL.
- `SECURITY_RULES.md`: Documented local bearer tokens, HttpOnly cookies, loopback isolation, single-host verification, Origin rejection on broker, non-destructive owned firewall rules, and lease expiry.
- `MODULES.md`: Detailed `companion/` internal packages and expanded frontend public measurement libraries.
- `ROADMAP.md` & `PRODUCT_REQUIREMENTS.md`: Detailed multi-tier product requirements (Public Web Helper, Windows Companion Preview, and Local Research Stack).
- `README.md`: Fully rewritten to present the three product facets, local start instructions, automated test summary, and viva presentation instructions.
- `plan.md`: Updated acceptance gate table for P0 through P12.

### 3. Open Risks & Blocked Boundaries
1. **Live Elevated Firewall Mutations (BLOCKED on host execution)**: Live rule creation and rollback are verified in memory-only PowerShell test fixtures; real host firewall mutations require explicit UAC administrator elevation.
2. **Elevated Broker Installation (DEFERRED)**: The preview runs the broker from user-writable Python. General distribution requires an Administrator-owned Program Files installation with hardened ACLs.
3. **Public Deployment (BLOCKED)**: The static export is verified in `public-release/dist`, but pushing to the live hosting endpoint (`https://netsentinel-connect.hariharan4814.chatgpt.site`) requires active operator session credentials.
