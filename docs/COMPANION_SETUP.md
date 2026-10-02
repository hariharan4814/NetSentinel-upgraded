# NetSentinel companion 0.2.0 - developer preview

**Unsigned source distribution; implementation and release verification are
unfinished. Read `YT.md` in the repository before continuing development.**
This package is prepared for review, not a signed or generally approved Windows
release. No successful install, privileged control or crash-recovery claim is
made by the existence of this archive.

## What it does

The local dashboard shows approximate application traffic and quotas, available
Defender/firewall status, explicit scan controls, observed flow metadata and
redacted PDF reports. It does not replace antivirus or measure ISP billable data.
The public website operates separately and cannot access this dashboard.

## Prerequisites

- Windows with Python **3.11, 64-bit**, installed from python.org. Installer
  accepts an explicit absolute `-PythonPath` if the usual per-user path differs.
- Network access during installation to download pinned, hash-checked official
  psutil7.2.2, Scapy2.7.0, ReportLab5.0.1, Pillow12.3.0 and
  charset-normalizer3.5.2 wheels. No downloaded script is executed via a web shell.
- Npcap installed separately by the user from https://npcap.com, after reviewing
  its license and capture privilege options. It is not bundled or automatically
  installed. Restricted driver access may require a separate authorized capture
  configuration; do not elevate a Next/Django web server to solve that.
- Defender/NetSecurity support varies by Windows edition, policy and installed
  antivirus. Unavailable or passive state is presented explicitly.

## Local developer setup from the repository

```powershell
cd C:\Users\yuvas\Desktop\NetSentinel
# Existing project environment can be used after installing requirements:
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements-companion.lock
.\.venv\Scripts\python.exe -m companion init
.\.venv\Scripts\python.exe -m companion serve
```

Open `http://127.0.0.1:8765`. The local key is in
`%LOCALAPPDATA%\NetSentinel\state\access.token`; view it privately and enter it
only in the local login form. Do not share, commit, log or paste it into a URL.
The broker uses a different `broker.token`. Private state contains sensitive
metadata and a SQLite database; keep it outside the repository/public artifact.

No capture, scan or block starts automatically on initial setup. Choose the
adapter and explicit capture checkbox to observe packet metadata. Apps may be
discovered from socket observations before capture, but missing bytes remain
unavailable observations. Packets are uniquely matched to recent socket owners;
ambiguity, missing privileges, fragments and stale snapshots leave bytes
unassigned. A flow segment is not a proven complete connection.

## Source installer preview

After reviewing the package and checksum, extract to a separate folder and run
`Install.ps1` as your regular user. It creates `%LOCALAPPDATA%\NetSentinel\app`,
its virtual environment and private state. It refuses to overwrite an existing
installation. No background service, startup task or driver is added. Scripts are
unsigned; follow your organization's policy rather than disabling machine-wide
PowerShell execution policy. A missing prerequisite fails explicitly.

Run installed `Start.ps1` without elevation, then visit the loopback URL above.
`Show-Access-Key.ps1` deliberately displays the key only when invoked locally.
`Stop.ps1` sends authenticated shutdown requests. Ctrl+C also requests normal
shutdown. Closing the browser locks access but does not stop native observation.

## Privileged broker - release blocker

**Do not treat the current per-user source installation as a hardened elevated
broker distribution.** Before general use, finish a separate administrator-owned
installation of its Python runtime, dependencies and broker code with protected
ACLs, and verify its fixed launch path. Mutable elevated Python files would defeat
the narrow HTTP command boundary. This required packaging work is tracked in
`YT.md`; no production broker installation is supplied in this preview.

For a reviewed, controlled development environment only, the existing
`Start-Broker.ps1` requires the operator to open an administrator shell explicitly.
It never prompts or elevates automatically. The broker binds127.0.0.1:8766,
requires its distinct key, rejects browser Origins, accepts only fixed operations
and resolves app IDs independently. Web servers remain non-administrative.

Enforcement is off by default. Enable it deliberately, then choose a non-critical
observed executable and quota. UTC daily/monthly reset times are shown. Warnings
and automatic quota blocking are separate choices. A temporary unblock lasts
until the next enabled quota reset. Rule application is **not** verified traffic
blocking; measure new connections, existing-connection behavior and overshoot.
Statistical anomalies never trigger automatic blocking.

## Stop, recovery and uninstall

Disable enforcement to request owned-rule cleanup. Normal service/broker shutdown
also attempts cleanup. The broker removes only exact NetSentinel-owned rules;
it never resets the firewall. Its service heartbeat lease expires after30seconds;
when the broker is alive it retries cleanup. If the broker itself crashes, rules
can remain until explicit recovery. Run `Recover.ps1` from an explicitly opened
administrator shell and inspect its result. Never uninstall the recovery tool
before confirming successful cleanup. Recovery/uninstall are not yet verified
on a clean Windows installation.

`Uninstall.ps1` supports only the default app path and first attempts stop and
recovery. By default it preserves private state. `-DeletePrivateHistory` explicitly
removes that private data directory; do not use it until backups/retention needs
are resolved. Npcap is never removed by NetSentinel. For a custom path, manually
stop/recover, verify the exact app path, and remove only that installation.

## Privacy, reports and retention

Usage buckets90days; flows7days/up to10,000; events90days/up to2,000;
destination context30days/up to5,000; apps up to512. The UI/report reads the latest
500 flow/event records. UTC is stored, display timestamps label local or UTC.
SQLite v1 stores metadata, settings and accounting only, not payloads, passwords,
cookies, URLs or message contents. Offline research ML and PostgreSQL remain
separate. Reports default to hidden paths/IPs, contain actual retained data,
and explicitly mark unavailable security information. Review PDFs before sharing.

Current tests use labelled SIMULATION fixtures. Hardware verification, resource
limits, quota overshoot, controlled actual blocking and scan completion remain
separate release gates documented in `YT.md` and `plan.md`.
