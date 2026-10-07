# Windows security and firewall adapters

Implemented 2026-10-02 for the Windows companion upgrade. These adapters are
independent of Django, Next.js, PostgreSQL and capture. They use only Python's
standard library and built-in Windows interfaces. No Windows binary or Defender
component is redistributed; NetSentinel implements integration code, not antivirus.

## Native process boundary

`companion/windows_security.py` resolves Windows' system directory with
`GetSystemDirectoryW`, then starts the absolute Windows PowerShell executable.
It does not resolve executables through PATH or trust a caller-provided SystemRoot.
The process uses `-NoProfile -NonInteractive -EncodedCommand`, hidden-window flags,
fixed module-owned scripts and absolute system module imports. Encoding is a
transport mechanism, not an authorization mechanism. The caller cannot provide
script text. Values go through a bounded JSON stdin message; they are never
interpolated into shell source. Native stdout and stderr are bounded independently
to 128 KiB. Input is limited to 8 KiB. Errors expose fixed codes, not native text
which can contain personal paths. No shell or elevation prompt is invoked.

Read requests time out after 20 seconds; firewall requests after 30 seconds.
A Defender scan request runs on one background worker, with a maximum 24-hour
wait. Terminating its PowerShell helper does **not** prove that Defender stopped
scanning. NetSentinel reports a timed-out scan request as `unknown` and never
silently cancels Windows protection. Applications should cache status for a short
interval rather than run overlapping expensive queries.

The authenticated privileged broker must be the only caller of mutation methods.
It must independently resolve observed application IDs, enforce protected apps,
check authorization and record control actions. These adapters are defense in
depth; they are not an HTTP authentication layer.

## Defender and firewall status

`SecurityProvider.status()` calls
[Get-MpComputerStatus](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus)
and retains actual antivirus/service/real-time booleans, running mode, signature
version/update time and available quick/full scan start/end timestamps. Times are
UTC ISO 8601; missing/invalid timestamps remain null. Signature age is computed
from the returned update timestamp and is null for unavailable or future dates.
Unknown flags remain null rather than false. `Normal`, passive, disabled, other
and unavailable states are distinct. No security score or safety verdict exists.

Defender can be disabled or passive with other antivirus software; this is an
environment state, not an installation error to repair automatically.
[Microsoft's compatibility documentation](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-compatibility)
describes those modes. NetSentinel does not enable Defender or change exclusions,
policies, real-time protection, signatures, or third-party antivirus settings.

[Get-NetFirewallProfile](https://learn.microsoft.com/en-us/powershell/module/netsecurity/get-netfirewallprofile)
reads `ActiveStore` for Domain, Private and Public. Each profile is represented
even if unavailable. These are configured profile settings, not a claim that all
three profiles apply to the current adapter. Default actions and the enabled
flag are reported separately. Partial Defender failures do not hide firewall data.

## Explicit scan controls and results

`start_scan(kind)` accepts exactly `quick` or `full`, after an active Defender
preflight. It invokes fixed
[Start-MpScan](https://learn.microsoft.com/en-us/powershell/module/defender/start-mpscan)
QuickScan or FullScan calls without a supplied scan path. Passive/disabled/missing
Defender and a concurrently tracked scan are rejected. The UI must require an
explicit user action for each scan, especially a full scan; no scan runs at startup.

`scan_status()` includes the tracked request and the latest actual Windows
observations. Its request can be `requested`, `running`, `completed`,
`completion_unconfirmed`, `unavailable`, `failed`, or `unknown`. A successful
cmdlet return alone is **not** completion. A newly observed start time and an end
time at or after that start support the running/completed display. To tolerate
Windows timestamps rounded to seconds, a newly changed start within one second
before the request can match. This is timestamp association, not a reliable scan
ID; a scan started elsewhere can overlap. No percentage is fabricated. A broker
restart loses in-memory request ownership; Windows' last available scan timestamps
remain visible and are not falsely labelled as a NetSentinel-owned scan.

[Get-MpThreatDetection](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpthreatdetection)
supplies at most 100 available detection records, containing IDs, timestamps,
action success and numeric Windows status/action identifiers. They are available
Windows history, not guaranteed newest-first results or results attributable to
the current scan. Resource paths, process names and raw errors are excluded.
An empty successful query means no records were returned; it does not mean the
computer is safe. Failed queries remain unavailable. Defender owns detection,
quarantine and remediation; NetSentinel never deletes or quarantines files.

## Owned application blocking

`FirewallController.block(executable, app_id)` accepts an existing canonical local
`.exe` and its SHA-256 identity calculated from
`ntpath.normcase(ntpath.normpath(executable)).encode('utf-8')`. UNC, device,
relative, wildcard, alternate-data-stream and noncanonical resolved paths are
rejected. The browser must send only an observed ID; the broker supplies the path.

Two rules are created in PersistentStore with
[New-NetFirewallRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule):

- Group: `NetSentinel.Companion.v1`.
- Names: `NetSentinel.Companion.v1.<sha256>.in` and `.out`.
- Description: `NetSentinel owned application block v1`.
- Enabled block action, inbound/outbound direction, all profiles/protocols,
  program bound to the validated executable.

An existing rule must have the expected ownership, direction, enabled state,
profile and program before it can be treated as an already applied rule.
If creation partly fails, only newly created owned rules are rolled back; failed
rollback names are returned for recovery. `success: true` and
`state: applied_not_traffic_verified` mean Windows accepted the rules. Group
policy, disabled profiles, filtering behavior and pre-existing flows can affect
traffic. NetSentinel does not turn a successful API call into a verified block.

`unblock(app_id)` rechecks exact group, ownership description and name before
removing those two rules. It can report partial removal. `cleanup()` removes only
matching owned rules, leaving unrelated or conflicting rules untouched; ownership
conflicts make its result unsuccessful. Rule enumeration is capped at 2,000
NetSentinel-group candidates. Read failures are never treated as absent rules.
No method resets the firewall, disables profiles, changes global defaults, or
removes user rules. Calls are serialized within one controller instance.

Native results contain `success`, `state`, `error` when relevant,
`traffic_blocking_verified: false`, `rule_names`, `removed`, `rollback_failed`,
`ownership_conflicts` and bounded `rules`. A failed operation may return without
raising: callers **must check `success`**. Interface/timeout/transport failures
raise `NativeOperationError` with a safe `.code`; validation raises `ValueError`.
Paths and arbitrary native error fields are not returned in rule-list responses.

## Verification evidence and remaining Windows gate

On 2026-10-02, the focused adapter command passed **31 tests** (including five
memory-only PowerShell fixtures) with no host firewall changes or Defender scans:

```powershell
$env:NETSENTINEL_POWERSHELL_FIXTURE = '1'
.\.venv\Scripts\python.exe -m unittest companion.tests.test_windows_security companion.tests.test_firewall -v
Remove-Item Env:NETSENTINEL_POWERSHELL_FIXTURE
```

Without that explicit test environment flag the five PowerShell integration
fixtures are skipped; the other 26 tests run. Their mock module is in-memory,
does not import native NetSecurity, and exercises the production script's actual
rule naming, partial failure rollback, rollback failure and ownership cleanup.
Initial native-script fixtures caught and fixed a PowerShell array-construction
bug; mocked Python calls alone had not caught it. The sandbox could not launch
the existing Python interpreter; rerunning with approved host execution worked.

Actual read-only adapter queries also succeeded: Defender returned Normal/active
with antivirus and real-time flags available, all three firewall profiles returned
enabled, and signature/scan history and detection-history availability were
reported. No private detection records were persisted. Owned-rule enumeration
returned success with zero owned rules and zero ownership conflicts. This proves
read compatibility on this machine, not scan execution or traffic enforcement.

Remaining: explicitly start a quick scan through the authenticated installed
companion, observe completion and error states, and use a disposable controlled
application for inbound/outbound traffic blocking, partial-failure recovery and
cleanup tests. Verify before/after new connections and preserve no private traffic.
Record actual elapsed time, overshoot, resources and firewall profile/policy context
in the release plan. Test a broker crash and restart cleanup, leaving unrelated
rules unchanged. Full scans require their own explicit user action. Signing and
native installation are separate release gates and are not claimed here.
