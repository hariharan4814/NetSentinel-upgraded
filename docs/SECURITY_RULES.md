# Security rules

## Initial Sprint 2 exception - 2026-09-13

The current user task explicitly defers authentication. This supersedes the
auth/enrollment requirements below for the initial four-model local API only.
No accounts, sessions, tokens or login endpoints are scaffolded. The runtime
requires environment-based secrets/PostgreSQL credentials, permits loopback
peers and fixed localhost Host values only, rejects Origin/cross-site browser
requests, and does not trust forwarded client IPs. No CORS or deployment is
provided. Local processes are unauthenticated and can access the data; loopback
checks are not identity authorization. Future exposure requires a new security
decision and authentication. Unknown request fields/payload blobs are rejected;
typed metadata is bounded and database errors are redacted. See ADR-023 and
[BACKEND_SETUP.md](BACKEND_SETUP.md).

Scope alignment, 2026-09-11: retain capture authorization, metadata privacy, provenance, trusted models and bounded processing for the four core modules. Replace the former mandatory enterprise roles/JWT/ticket design with minimal local access. This supporting update prevents a conflicting security plan from recreating removed features; it changes no code or Sprint 1 acceptance rule.

## Trust boundaries and threats

Treat browsers, uploaded replay files, sensor input, model artifacts, external APIs and all free-text fields as untrusted. Main threats include unauthorized metadata access, compromised sensor injection, session/credential theft, cross-mode contamination, malicious pickle loading, parser/resource exhaustion, report leakage, and unauthorized capture. A compromised sensor can falsify its own observations; authentication establishes source identity, not factual truth.

Initial deployment is a single trusted local workspace. Bind services to loopback by default and keep database access separate from sensor credentials. Use HTTPS/WSS whenever traffic leaves loopback. Do not describe development settings as production deployment hardening.

## Identity and authorization

- Use Django's built-in password/session facilities for a minimal local operator where authentication is needed. Session cookies are HttpOnly and SameSite; use Secure over HTTPS and document the explicit loopback development exception. Protect cookie-backed mutations against CSRF, throttle login and invalidate server-side sessions on logout. Confirm exact settings during authorized Sprint 2 setup.
- Authorize REST data access, ingestion and every sensitive action server-side. Hidden buttons, a mode selector and loopback binding alone are not authorization. No administrator/analyst/viewer hierarchy or user-management product is required.
- Configure allowed hosts and exact trusted origins. Prefer a same-origin local frontend/backend path; if origins differ, use narrowly configured CORS/CSRF settings. No wildcard credentialed access.
- Provision a separate scoped, revocable sensor upload credential, stored hashed when verification permits. Restrict source/mode/session access and local secret files. Sensor credentials cannot call operator routes, execute arbitrary commands or control Windows settings.
- Capture start/stop remains a locally authorized operator action. Enrollment revocation denies subsequent uploads but cannot stop an offline process. Local stop remains available. No silent driver installation, elevation, scanning, blocking or network reconfiguration.
- Training, trusted artifact selection/load and isolated lab launch remain explicit local operator/CLI operations with bounded configuration and recorded actual versions. No arbitrary uploaded model execution.
- WebSockets are conditional on a later measured need. If adopted, authenticate and authorize every subscription/event by scope/mode, validate Origin, enforce expiry and prompt revocation, and reauthorize after reconnect. Never assume HTTP login automatically secures a socket.

Historical multi-role RBAC, SimpleJWT refresh rotation, session-version/socket-ticket orchestration, administrator consoles and remote capture commands are **OUT OF SCOPE as required infrastructure**. Equivalent basic protection is still mandatory for the actual session/transport chosen; no anonymous sensitive endpoint is implied. A lab source has separate run/state/credential context and never transmits simulated packets.

## Data minimization and safe processing

Persist network metadata and aggregates only by default. Payloads, credentials, cookies, full URLs, and message contents are not collected features. IP/MAC addresses and topology still reveal sensitive information; restrict access and redact examples/screenshots used in public submissions. Avoid DNS query storage initially.

“No payload storage” includes library packet retention, TShark temporary files, debug prints, error dumps and transport quarantine. Extract only whitelisted metadata and discard packet objects. Header-length/snaplen limits reduce exposure but do not guarantee that captured bytes exclude payload. Disable automatic DNS/name enrichment; SSID/BSSID and MAC/IP history may reveal location or identity and require minimization. Database/spool/backup permissions and age/size cleanup apply from the first persistence sprint. A reviewed research-feature export needs an explicit expiry and redaction plan.

Validate schemas, sizes, timestamps, bounded counts, provenance, file types, file paths and all references server-side. Do not execute uploaded content or shell-interpolate user values. Replay files require quotas, parser timeouts, isolated low-privilege processing and controlled file names; never let a path escape the input directory. A PCAP may contain payloads even when the output is metadata: use restricted temporary storage and default deletion after processing.

Load joblib/pickle artifacts only from a trusted local training workflow after local operator review and digest verification. A hash detects change, not trustworthy authorship. No arbitrary uploaded model deserialization. Record provenance and version compatibility; do not expose model paths as unrestricted download routes.

Approval also verifies feature semantics, observation profile and allowed mode; a matching vector length or dataset column name is insufficient. A selected model is not applied until the sensor records the actual loaded version at a window boundary. Network-provided thresholds/configuration require schema validation and bounded computation. Invalid analysis cannot disable collection or trigger enforcement.

Escape UI text and redact private metadata in academic screenshots/report evidence. If a later authorized research CSV export exists, neutralize formula prefixes, protect access and set expiry; a reporting product is not required. Exclude secrets/private payloads from logs. Maintain bounded ingestion, sockets, jobs, queries, queues and disk usage to resist accidental or malicious exhaustion.

## Audit, secrets and operations

Keep a minimal bounded sanitized log of actor/source, action, outcome and UTC time for authentication failures, denied sensitive actions, credential changes, local capture/model/lab operations and retention failures. Include request IDs for API events. Incident transitions and enterprise audit/export workflows are OUT OF SCOPE. Sanitize details; never log passwords, tokens or full ingestion bodies. Append-only application APIs and restricted DB roles reduce tampering, but local database administrators can still modify data.

Environment variables configure secrets; examples contain placeholders only. Ignore rules are a convenience, not a secret scanner. Check staged content before commits; if a secret leaks, revoke/rotate it and address repository history appropriately. Preserve dependency lockfiles once implementation begins, select supported versions then, and review vulnerability/license findings before release.

Use migrations and tested backups/restores. Retention covers database rows, generated files, spools and backups; document delayed deletion in backups and data-file space reuse. Never reset a database as a routine upgrade. Elevate only capture when necessary, not Django/Next.js. A single-ASGI-process in-memory channel layer is local-demo-only, not a production security/reliability claim. Neither Redis nor an unsupported native-Windows Celery worker is a default dependency.

## Removed integrations — OUT OF SCOPE

Bluetooth monitoring, external threat intelligence, AI chatbots and LLM explanations are removed from active delivery. No metadata is transmitted to these services. Explainable Threat Analysis uses observed statistics and transparent local rules. Network topology, enterprise notifications, advanced RBAC, remote-device claims and cloud deployment are also OUT OF SCOPE; preserve privacy and authorization for the smaller local system.
