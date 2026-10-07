# Local research monitor authentication

Implemented for the 2026-10-02 upgrade. This supersedes earlier documentation
that deliberately left the Django API and `/local` monitor unauthenticated.
The public static connection helper remains usable without a password. The
separate Windows companion has its own authentication and privilege boundary.

## Configure once, without administrator privileges

Use a password manager to generate four **different** random secrets (recommended
64 hexadecimal characters). Accepted length is 32–256 printable non-space ASCII
characters. Example files deliberately contain unusable placeholders.

1. In the ignored repository `.env`, configure `NETSENTINEL_READ_TOKEN`,
   `NETSENTINEL_INGEST_TOKEN`, and `NETSENTINEL_MODEL_TOKEN`, alongside the existing
   Django/PostgreSQL settings. Do not replace unrelated existing values.
2. In ignored `frontend/.env.local`, set the same `NETSENTINEL_READ_TOKEN`, a
   different `NETSENTINEL_OPERATOR_PASSWORD`, and the existing loopback
   `BACKEND_API_BASE_URL` (normally `http://127.0.0.1:8001/api/v1/`).
   Never prefix a secret with `NEXT_PUBLIC_`.
3. Restart Django and Next. Keep both bound to `127.0.0.1`; use the existing local
   launch procedures. Do not run them as administrator or reverse-proxy them.
4. Open `http://127.0.0.1:3000/local` and enter the operator password. A missing
   configuration fails closed and the page explains the required setup.

Protect the local files with your Windows user account. Do not paste secrets into
Git, bug reports, screenshots, PDFs or command-line arguments. Existing `.env`
files are never modified automatically by this upgrade. Old running processes
must be restarted to pick up authentication changes.

## Credential scopes and API contract

| Credential | Accepted actions |
| --- | --- |
| Operator password | Sign in to this local Next process; never sent to Django |
| Read token | Django GET reads, including health; kept server-side by Next |
| Ingestion token | POST monitoring-sessions, telemetry, windows, capture-status |
| Model token | POST model-versions and anomaly-results metadata |
| `NETSENTINEL_LAB_TOKEN` | POST lab jobs and cancellation only |
| `NETSENTINEL_LAB_WORKER_TOKEN` | POST lab claim, heartbeat and finish only |

Django requires `Authorization: Bearer <token>`. It accepts no browser cookies,
rejects any Origin header and same-site/cross-site browser requests, requires an
actual loopback peer and an allowed loopback Host, and trusts no forwarded
headers. Missing/invalid/unconfigured credentials return 401. A valid credential
outside its method/route scope returns 403. Reused keys fail closed; a read key
cannot ingest, and an ingestion key cannot read or publish models. No credential
provides Windows capture, firewall, model execution or arbitrary-command access.
The scope is one trusted local research publisher across its supported source
IDs and LIVE/SIMULATION/REPLAY modes; this is not multi-tenant sensor enrollment.
Existing source/session/provenance validation still applies.

Next's GET relay requires a logged-in session. It constructs a fixed allowlisted
upstream URL, supplies only its server-held read token, rejects redirects, and
never forwards the browser's cookie, Authorization, Origin or arbitrary path.
No local authentication route is included in the public source allowlist.

## Browser sessions, CSRF and revocation

`GET /api/local-auth` returns 401 without a session, or the current session's
CSRF token and expiry after login. `POST /api/local-auth` accepts only a JSON
`password` object of at most 2,048 bytes. Login and logout require an exact
same-origin Origin and `X-NetSentinel-Request: local-ui-v1`; logout additionally
requires the session's `X-CSRF-Token`. Cross-origin login and logout fail.

Sessions use random opaque 256-bit identifiers, stored hashed in server memory,
with `HttpOnly`, `SameSite=Strict`, four-hour cookies and a maximum of 16 live
sessions. HTTP-only loopback is an explicit exception to `Secure` cookies; do not
expose this server to a network. Five failed attempts throttle login for one
minute. The local process shares this limit; a hostile local process can cause a
temporary lockout but cannot bypass authentication through forwarded headers.

Sign out revokes the server-side session as well as expiring the cookie. All
sessions end on a Next restart. Rotating either Next secret invalidates existing
sessions after restart. Expiry is rechecked server-side for every data request;
the UI rechecks the session every 30 seconds. This memory session store supports
one local Next process, not multi-worker/cloud hosting. Already viewed/downloaded
data cannot be revoked. No credential protects against malware running as the
same Windows user and able to read that user's private files or process memory.

## Publishing research data

The independent sensor still runs without Django, tokens, PostgreSQL or a model.
It currently has no production HTTP upload adapter. Its local outputs and
scientific contracts are unchanged.

For the existing explicitly invoked `python -m ml publish ...` CLI, supply
`NETSENTINEL_INGEST_TOKEN` in that process's environment. Publishing a model and
scores also requires `NETSENTINEL_MODEL_TOKEN`. The CLI does not read `.env`
automatically and never takes tokens as command-line flags. Missing keys stop
before HTTP. It uses the correct key per route, refuses proxies/redirects and
remote origins, keeps its existing five-second timeout and 65,536-byte record
limit, and does no automatic retry. Importing/training/scoring ML remains offline.

## Verification

Run the backend command **from `backend`** so Django discovers the backend's
`tests` package, rather than the root's unrelated sensor tests:

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\backend
..\.venv-backend\Scripts\python.exe manage.py test tests --settings=config.test_settings
..\.venv-backend\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
cd ..
.\.venv-ml\Scripts\python.exe -m unittest discover -s tests -p test_publication_auth.py
cd frontend
npm test
npm run typecheck
npm run lint
npm run build
npm run test:e2e
```

Browser regressions use explicit test-only credentials and synthetic responses.
The unmocked route test verifies actual login cookies, logout revocation, denial
of unauthenticated reads and the private GET relay's server-held header. These
tests do not prove production database reachability or live capture.

Manual Windows check: restart the two unprivileged services; verify unauthenticated
reads return 401; sign in, select a known retained session, verify its provenance;
sign out and repeat the read; change one key/restart and confirm old cookies fail.
Stop Django and verify the dashboard reports unavailable without discarding
previously labelled historical observations. Restore Django and verify recovery.
No migrations are introduced by authentication.

## AI Lab runtime additions — 2026-10-05

For manual lab startup add two further distinct random secrets: the lab token
to Django and Next; the worker token to Django and the independent worker only.
The worker reads its credential from the process environment, not a CLI flag or
the repository `.env`. Never give the browser or Next the worker token. Next's
operator password and read token continue to be required. `/lab` shares the local
operator session; lab mutations additionally require its CSRF token, exact local
Origin and `X-NetSentinel-Request: local-ui-v1`.

Select `config.lab_settings` explicitly for a standalone simulation demonstration.
It uses `NETSENTINEL_LAB_DATABASE_PATH` (default ignored
`artifacts/lab/demo.sqlite3`), installs only the experiments app, and exposes no
research telemetry/model routes. Supply `DJANGO_SECRET_KEY` of at least 50
characters and the three distinct read/lab/worker tokens. There are no built-in
runtime credentials and the original test-settings runtime prohibition remains.
Original `config.settings` remains PostgreSQL; no private data is copied.

After configuring secrets in your environment:

```powershell
.\.venv-backend\Scripts\python.exe backend/manage.py migrate --settings=config.lab_settings
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001 --noreload --settings=config.lab_settings
# Separate ordinary terminal, with only the worker token supplied:
.\.venv-lab\Scripts\python.exe -m lab.worker --base-url http://127.0.0.1:8001 --artifact-root artifacts/lab/worker
```

No administrator privileges, Npcap, PostgreSQL, security changes or external
network calls are needed for simulation. Stop the worker with Ctrl+C: it
terminates its own fit process and requests cancellation. If the backend cannot
be reached, the 30-second lease marks the job interrupted on the next operation.
An interrupted model fit is never resumed or presented as complete.
The spawned fit also watches its parent's process handle and exits if the worker
dies abruptly; it does not rely on a reusable PID. This behaviour has a Windows
spawned-process regression, in addition to mocked cancellation/timeout tests.

Worker artifact cleanup only removes marked UUID subdirectories it owns; other
files remain. The default maximum is 20 runs and a 500 MiB root budget, checked
between heartbeat intervals. The fit has a 600-second time limit. These are
application bounds rather than an OS disk/memory sandbox; a local account remains
trusted. Use a dedicated artifact directory, separate from the SQLite database.
