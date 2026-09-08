# Security rules

## Trust boundaries and threats

Treat browsers, uploaded replay files, sensor input, model artifacts, external APIs and all free-text fields as untrusted. Main threats include unauthorized metadata access, compromised sensor injection, JWT theft, cross-mode contamination, malicious pickle loading, parser/resource exhaustion, report leakage, and unauthorized capture. A compromised sensor can falsify its own observations; authentication establishes source identity, not factual truth.

Initial deployment is a single trusted local workspace. Bind services to loopback by default and keep database access separate from sensor credentials. Use HTTPS/WSS whenever traffic leaves loopback. Do not describe development settings as production deployment hardening.

## Identity and authorization

- Use Django password handling and SimpleJWT with short-lived access tokens, refresh rotation/revocation and login throttling. Proposed lifetimes are 10 minutes access and 1 day refresh, subject to the setup sprint.
- Keep access tokens in memory and refresh tokens in Secure, HttpOnly cookies for deployed HTTPS; protect cookie-backed endpoints against CSRF. Explicitly document any localhost development exception. Do not store long-lived tokens in localStorage.
- SimpleJWT does not supply the proposed cookie/CSRF or immediate access-token/socket revocation behaviour automatically. Plan explicit views/middleware, refresh blacklist support and a server-side auth/session version checked on each protected request. Socket consumers recheck at least every 5 seconds and at expiry. Logout/role change revokes server-side access state as well as refresh eligibility; no promise of zero-delay socket revocation.
- Configure allowed hosts, exact CORS origins and WebSocket origin checks. Authenticate sockets using short-lived single-use tickets and enforce scope/mode on subscriptions and events.
- Enforce least privilege using API_PLAN.md roles for every action and object lookup. Hiding buttons is not authorization. Role revocation must invalidate ongoing sensitive access, including sockets.
- Enroll sensors with scoped, revocable credentials, stored hashed by the backend when verification permits. Restrict local secret files using OS permissions. Sensor credentials do not grant human access or arbitrary command execution.
- Require administrator permission for capture scope, sensor credentials, model activation, role changes and retention policy. Analyst lab runs must remain isolated. Never auto-block a device from an anomaly score.

MVP capture is a locally authorized operator action; the backend controls enrollment/uploads, not the existence of offline local monitoring. Enrollment revocation prevents upload immediately on subsequent authentication checks but cannot stop an offline process. Local stop must remain available. Advanced web capture requests require both backend authorization and local operator acceptance and cannot install drivers/elevate privileges. Keep a separate lab-scoped credential/configuration, bounded run state and no network packet transmission in simulation.

## Data minimization and safe processing

Persist network metadata and aggregates only by default. Payloads, credentials, cookies, full URLs, and message contents are not collected features. IP/MAC addresses and topology still reveal sensitive information; restrict access and redact examples/screenshots used in public submissions. Avoid DNS query storage initially.

“No payload storage” includes library packet retention, TShark temporary files, debug prints, error dumps and transport quarantine. Extract only whitelisted metadata and discard packet objects. Header-length/snaplen limits reduce exposure but do not guarantee that captured bytes exclude payload. Disable automatic DNS/name enrichment; SSID/BSSID and MAC/IP history may reveal location or identity and require minimization. Database/spool/backup permissions and age/size cleanup apply from the first persistence sprint. A reviewed research-feature export needs an explicit expiry and redaction plan.

Validate schemas, sizes, timestamps, bounded counts, provenance, file types, file paths and all references server-side. Do not execute uploaded content or shell-interpolate user values. Replay files require quotas, parser timeouts, isolated low-privilege processing and controlled file names; never let a path escape the input directory. A PCAP may contain payloads even when the output is metadata: use restricted temporary storage and default deletion after processing.

Load joblib/pickle artifacts only from a trusted local training workflow after administrator approval and digest verification. A hash detects change, not trustworthy authorship. No arbitrary uploaded model deserialization. Record provenance and version compatibility; do not expose model paths as unrestricted download routes.

Approval also verifies feature semantics, observation profile and allowed mode; a matching vector length or dataset column name is insufficient. A requested model is not applied until the sensor acknowledges its actual version. Network-provided thresholds/configuration require schema validation and bounded computation. Invalid analysis cannot disable collection or trigger enforcement.

Escape UI text, sanitize report output and neutralize spreadsheet-formula prefixes in CSV exports. Reauthorize report download, use expiring files and exclude secrets/private payloads from logs. Maintain bounded ingestion, sockets, jobs, queries, queues and disk usage to resist accidental or malicious exhaustion.

## Audit, secrets and operations

Record actor, action, object, outcome, UTC time and request ID for authentication security events, denied sensitive actions, enrollment, capture changes, model lifecycle, policy changes, incident transitions, lab runs and exports. Sanitize details; never log passwords, tokens or full ingestion bodies. Append-only application APIs and restricted DB roles reduce tampering, but local database administrators can still modify data.

Environment variables configure secrets; examples contain placeholders only. Ignore rules are a convenience, not a secret scanner. Check staged content before commits; if a secret leaks, revoke/rotate it and address repository history appropriately. Preserve dependency lockfiles once implementation begins, select supported versions then, and review vulnerability/license findings before release.

Use migrations and tested backups/restores. Retention covers database rows, generated files, spools and backups; document delayed deletion in backups and data-file space reuse. Never reset a database as a routine upgrade. Elevate only capture when necessary, not Django/Next.js. A single-ASGI-process in-memory channel layer is local-demo-only, not a production security/reliability claim. Neither Redis nor an unsupported native-Windows Celery worker is a default dependency.

## Optional integrations

Bluetooth requires explicit local permissions and must not silently merge presence with IP identity. External threat intelligence and LLM use remain opt-in with redacted metadata and documented transmission. An AI explanation cites stored evidence, discloses uncertainty, treats network strings as untrusted input, and cannot execute remediation or confirm an attack independently.
