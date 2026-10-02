# NetSentinel handoff to Google Antigravity

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

This section is completed by Codex during WIP stabilization below. It is the
authoritative final stopping record; earlier milestone counts are historical.
