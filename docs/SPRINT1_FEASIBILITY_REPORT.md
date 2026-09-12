# Sprint 1 feasibility evidence

## Final Sprint 1 sign-off - 2026-09-12

**Sprint 1: PASS for the selected Ethernet 3 own-host observation profile.**
All S1-01 through S1-08 rows have evidence below. This supersedes older PARTIAL,
"not run", cadence-rerun and missing-sink statements. No acceptance threshold
was weakened. No sensor production code changed during this sign-off; its
previously corrected scheduler and all recovery/scientific constraints remain.
No Django, PostgreSQL, Next.js, model or Sprint 2 implementation was started.

### Exact acceptance matrix

| Gate | Final status and evidence |
| --- | --- |
| S1-01 Environment | PASS, Ethernet 3 only. Historical Windows/laptop, Samsung USB driver, Npcap 1.88/access/mapping evidence retained. Current preflight and selected mapping succeeded at index 23; Windows build 26200, Python 3.11.0, Scapy 2.7.0 and psutil 7.2.2 rechecked. No driver/settings/privilege changes. |
| S1-02 Independent visible operation | PASS. Accepted 1,800.016-second run, 1,799 valid health records, all checks true, exit 0; five-minute operator-idle confirmation and sixty successful controlled requests. p95 flushed sample delay 0.008081 seconds, below 2 seconds. No backend/model required. |
| S1-03 Packet/window correctness | PASS. Operator-reported matched live TCP reference has exact agreement on all six counts below; fresh TCP/UDP capture and exact UDP length accounting repeated here. Accepted p95 window processing after lateness 0.047712 seconds, below 1 second. Ten-second windows and live host-v1 generation observed; fixture arithmetic remains exact. |
| S1-04 Visibility/attribution | PASS for host-first scope. Historical capability matrix retained. Only the selected observation point is proven; remote-device attribution, hotspot and monitor-mode claims remain unsupported/experimental, not additional product requirements. |
| S1-05 Failure/resource bounds | PASS. Accepted run peak working set 81,756,160 bytes, bounded queues/flows, no known application loss, and 0.016-second shutdown/overrun. Memory review below passes. Existing offline tests cover pressure/drop accounting, idle versus stopped, unavailable adapter/permissions, restart and equivalent clock-gap handling. Actual unavailable loopback HTTP sink with continuing local output demonstrated below. Recovery evidence reviewed separately. |
| S1-06 Privacy/scope | PASS for inspected code/artifacts. One explicitly authorized interface; non-promiscuous IP filter; metadata/aggregates only, no payload dumps, model artifacts, scans, blocking or hidden installation/elevation. Controlled HEAD/DNS activity is opt-in. HTTP fixture destination is loopback only. Private endpoint/process logs stay in ignored tmp/. |
| S1-07 Frozen minimum contract | PASS. Unchanged host-v1 definitions and hand-calculated zero/bidirectional/boundary/missing-header fixtures; new live run produces seven finite values for a complete window and null for partial windows. No model/accuracy claim; unknown kernel loss and unsupported metadata remain explicit. |
| S1-08 Repeatability/decision | PASS. Independent fresh processes on the corrected sensor completed startup, TCP/UDP capture, windows/features and shutdown, exit 0. Earlier repeats remain historical corroboration; they alone were insufficient to verify the scheduler change. Final host-profile PASS is recorded here. |

### Accepted thirty-minute log, idle and memory review

Audited all records in private `tmp/sprint1-cadence-20260912-213705.jsonl`;
SHA-256 `0234ec00ca1fb5ad33405261239331c1de651e6296e236fdaada72f9f86df598`.
The sibling exit file contains 0; the process journal contains normal worker
join/socket-close, validator-return 0 and interpreter-atexit markers.
The run lasted 1,800.016 seconds, with 1,799 valid samples, 181 windows,
116,133 packets and 73,603,839 IP bytes. All ten automated checks are true.
Sixty controlled attempts all succeeded. Interface losses/recoveries/gaps,
parser/flow errors, queue drops/remainder, overflow and late counts are zero.
Queue/flow/window high-water marks are 353 / 220 / 2. Average sample interval
is 1.000044 seconds; p95 is 1.046 seconds. No full rerun is needed for the
test-only evidence changes made in this task.

**Idle review: PASS.** The operator explicitly confirmed in this session that
the first five minutes had no intentional browsing/downloads/streaming or other
generated activity. Those 299 samples cover the low-idle phase, with 3,015,346
OS bytes of ambient traffic and process CPU averaging 4.278% on psutil's process
scale. Idle does not mean zero traffic. No artificial idle-byte threshold was
introduced; counters alone would not establish the operator's activity.

**Memory review: PASS for this run.** All working-set measurements are below
500 MiB; peak 81,756,160 bytes, final stop RSS 45,645,824 bytes. The first health
RSS is 79,360,000 and the last is 45,404,160 bytes. The trajectory is not a
persistent one-way increase:

| Run interval | Health samples | Mean RSS, bytes | Observed OS bytes |
| --- | --- | --- | --- |
| 0-300 seconds | 299 | 80,340,341 | 3,015,346 |
| 300-600 | 300 | 44,911,548 | 3,835,503 |
| 600-900 | 300 | 25,816,951 | 2,723,359 |
| 900-1200 | 300 | 23,447,948 | 4,682,026 |
| 1200-1500 | 300 | 20,674,970 | 3,005,530 |
| 1500-1800 | 300 | 33,074,053 | 57,902,945 |

During the busier final phase RSS reaches about 53.0 MB, then falls to 45.4 MB
before shutdown. This supports bounded measured behaviour and presents no
unexplained persistent working-set growth requiring another Sprint 1 run.
Correlation with activity does not establish an allocator/OS mechanism. RSS
alone cannot prove absence of every memory leak or predict indefinite uptime.

### Fresh-process and matched traffic evidence

Sensor `capture.py` SHA-256 for the fresh runs:
`b148350aa6f0c6bd3b4b866f85c9066f5e71423fda627782875303d47fd6f7ba`.
All sensor Python files match their task-start hashes; changes are confined to
test/validator support and documentation.

- `tmp/sprint1-final-fresh-20260912T164323Z/`: fresh process PID 21884,
  exit 0; `manual_live.py --interface "Ethernet 3"`, 24-second capture.
  Startup/normal duration shutdown observed, shutdown 0.031 seconds; 23 health
  records, 3 windows, 11,930 total packets / 9,553,710 IP bytes, no loss/errors.
  Controlled TCP: 10 packets / 707 IP bytes, 5 each direction, 273 outbound /
  434 inbound bytes. Controlled UDP: 1 packet each direction, 57 outbound /
  89 inbound IP bytes, exactly DNS payload lengths plus 28 bytes. Windows in
  this particular run are partial and correctly have null features.
- `tmp/sprint1-final-outage-20260912T164707Z/`: fresh process PID 27840,
  exit 0, 24-second capture plus initialization/final output (25.5 seconds parent
  wall time). 23 valid health records, 4 windows, 14,785 packets / 11,867,007 IP
  bytes. Controlled TCP is bidirectional (16 packets / 1,069 IP bytes);
  controlled UDP again exactly 2 packets / 146 IP bytes. A complete ten-second
  window yields seven host-v1 values, including 691.5 packets/s and 568,679.1
  IP bytes/s; partial windows remain null. This is genuine metadata-derived
  output, not model scoring. Shutdown is below monotonic timer resolution
  (reported 0.0 seconds), not a claim of instantaneous cleanup. Duration stop,
  clean socket/worker return, no errors/loss and exit 0 observed.

The **separate matched TCP reference** supplied by the operator for the corrected
sensor reports reference/captured packets 10/10, IP bytes 707/707, outbound
packets 5/5, inbound packets 5/5, outbound bytes 273/273, inbound bytes 434/434:
all discrepancies **0%**, `passed=true`. No separate saved reference-result
file was found in tmp/; this is explicitly operator-supplied evidence, not a
claim that this task reran the dual-reader reference script. The first fresh
manual run independently reproduces those controlled counts, but is not itself
an independent reference. The existing same-interface/filter/exchange reference
validator and fixtures retain their <=5% gate and shared Npcap/offload limits.

### Actual HTTP-outage independence

**PASS at the Sprint 1 sensor emission boundary.** Added the focused opt-in
`manual_live.py --http-outage` fixture and `http_outage.py`, without changing
the production sensor or implementing an ingestion service. The fixture binds
and reserves a loopback port without listening, then attempts a real HTTP POST
of the first actual health record with a 0.2-second socket timeout. Local
metadata is delivered/flushed first. The expected failure opens a circuit for
the remainder of this finite validator process: no retries and no upload queue.
Undelivered records are counted explicitly; local sensor records are unmodified.

The final evidence directory above contains `stdout.json`, `local-output.jsonl`
and `process.json`. Observed HTTP `TimeoutError`, one attempt, zero accepted,
23 discarded upload copies, zero queued. After the failure record, local output
contains **22 health records, four windows, STOPPED and capture_stopped**.
Controlled HEAD/DNS activity begins only after the HTTP failure; both exchanges
are captured and verified. Normalized packets increase from 226 at failure to
14,785 at shutdown. Capture queue high-water 269, flow high-water 80, two windows,
zero application losses/errors/remainder. `http_outage.passed=true`, exit 0.

A preliminary outage run at `tmp/sprint1-final-outage-20260912T164618Z/` passed
local in-memory delivery and traffic checks; it was followed by the final run
after adding flushed per-record local output. Only the final run is used for
the visible-output outage gate. Four offline tests cover refusal/timeout/HTTP
failure containment, HTTP 503, unexpected success not being called an outage,
and preservation of local-output exceptions. They also check exact local
record preservation, connection closure, a single attempt and counted discards.

This closes the original S1-05 outage requirement with an actual optional HTTP
consumer attached to the real sensor, not an unrelated preflight exception.
It does **not** certify future Django ingestion, credentials, retry/spool/durable
delivery or reconnect semantics; those require their own integration tests when
authorized. No localhost service, backend/database, cloud endpoint, dependency,
or production HTTP client was added. See ADR-022.

Reproduce this bounded evidence from repository-root PowerShell:

```powershell
.\.venv\Scripts\python.exe tests/sensor/manual_live.py --interface "Ethernet 3" --http-outage
$LASTEXITCODE
```

### Recovery, historical termination and final decision

The unexplained 2026-09-09 exit remains **historical, cause unproven**. It must
not be relabelled as a fixed native crash, blamed on an adapter, or conflated
with the separately demonstrated cadence defect.

The 2026-09-12 recovery diagnostic has five successful restarts and normal
duration cleanup after 480.125 seconds, with 21.251 seconds of explicit gaps.
Its final worker join/socket close and STOPPED are recorded at Unix UTC
1789204674.1257; the observer's operator interruption follows at
1789204674.461919 (about 0.336 seconds later). Validator-return and atexit markers
are present. Thus recovery cleanup evidence precedes the observer intervention;
the intervention still qualifies the externally observed exit. The earlier
abrupt exit's cause is not established by this ordering.

The accepted subsequent uninterrupted run, current fresh-process clean exits,
and unchanged recovery/clock-gap/identity/shutdown regression tests are
**sufficient for Sprint 1 sign-off on this host profile**. A historical unknown
without recurrence in the accepted evidence is retained as a limitation, not
an invented new mandatory crash-reproduction gate. No guarantee of arbitrary
future driver stability, hard real-time blocked-output shutdown, zero kernel
loss, physical-wire accuracy or other-device visibility is made.

Full suite: **93/93 passed in 4.295 seconds**, exit 0, using
`.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`.
`git diff --check`: PASS, exit 0. All existing tests retained. Private logs stay
ignored; only sanitized observations are documented. **Remaining unmet Sprint 1
gates: none. Sprint 1 final status: PASS.**

**Exact next task:** review/preserve this acceptance record and the private
evidence. Await a separate explicit Sprint 2 implementation request; do not
start its backend or dependencies as part of this sign-off. No further live
run is required solely for the test/documentation additions here.

## Sample coverage investigation and cadence fix - 2026-09-12

**PARTIALLY PASSED / NO-GO for Sprint 2.** The official Ethernet 3 run completed
1,800.031 seconds with normal cleanup, but correctly failed sample coverage.
The sensor scheduling fix below requires a new uninterrupted thirty-minute run.
This section supersedes older "not run" and next-command statements; historical
recovery/termination evidence is retained without claiming its cause was fixed.

### Full-log audit and exact failure

Read every record in private `tmp/sprint1-usb-acceptance.jsonl` (UTF-16).
SHA-256: `2225aefd1a87fec581c7517f0d79309d2a4e6954b68dd5564fe269037be03c81`.
All 1,674 records parsed: one start, two statuses, 1,669 health records, one
stop and one final summary. One health session, no duplicate observation times,
all health records valid with null reason. Every adjacent cumulative counter
difference equals the recorded delta. The summary count agrees with the file.
Window details are intentionally suppressed by the harness; its summary reports
181 windows, 20,318 packets and 9,331,106 IP bytes with conservation true.

The exact unchanged predicate in `tests/sensor/stability_live.py` is
`len(samples) >= 1700 and all(r["valid"] for r in samples)`.
It fails the count branch only: **1,669 < 1,700**, short by **31 records**.
Against the nominal 1,800 one-second opportunities, actual coverage is
**92.7222%**, required **94.4444%**, a **1.7222 percentage-point** shortfall.
These percentages describe sample cadence, not packet capture completeness.
The code uses an absolute count, not a percentage or a p95-interval threshold.
The actual-duration denominator (1,800.031) would give 92.7206%; it is not the
acceptance denominator. All nine other automated checks are true; exit 2 is the
expected code path, also reported by the operator (not independently stored as
an OS exit code in this JSONL).

| Measurement | Full-run evidence |
| --- | --- |
| Health interval min / mean / median / p95 / max | 1.046 / 1.0779095 / 1.078 / 1.094 / 1.125 seconds |
| First / last health run time | 1.109 / 1,799.031 seconds |
| Sum of measured health intervals | 1,799.031 seconds; 130.031 seconds above 1,669 nominal seconds |
| Low-idle / controlled / normal sample counts | 278 / 278 / 1,113 |
| Mean interval by phase | 1.078518 / 1.077730 / 1.077802 seconds |
| p95 sample-end through flushed print | 0.002485 seconds (limit 2) |
| p95 window processing after lateness | 0.082650 seconds (limit 1) |
| Controlled attempts / successes / errors | 60 / 60 / 0 |
| Peak / final RSS | 83,062,784 / 83,021,824 bytes; peak 79.215 MiB, below 500 MiB |
| Queue / flow / window high-water | 379 / 92 / 2 |
| Shutdown / duration overrun | 0.016 / 0.031 seconds; no shutdown error |
| Interface loss / recovery / monitoring gap | 0 / 0 / 0 |
| Parser / flow errors / queue drops / overflow / late / queue remaining | All zero |

### Evidence-backed cause and limits

The sensor `_run_capture` waited until `now_mono - last_check >= 1`, then
revalidated interface/address state and read OS counters, then set `last_check`
to the counter-read completion time. Thus each interval included a fresh second
of waiting **plus** synchronous collection time and polling overshoot. That
overhead accumulated rather than being absorbed into a fixed cadence. The actual
130.031 seconds of accumulated excess explains the count shortfall; there is no
isolated multi-second hole (maximum interval 1.125 seconds). Adjacent timestamp
versus recorded-interval differences are at most 0.016 seconds, consistent with
timestamp/emit timing resolution, not missing one-second records.

A separate read-only, no-capture probe on this laptop performed 30 calls per
operation: mean interface validation 40.988 ms, address validation 15.610 ms,
counter read 16.166 ms, combined 72.764 ms. This corroborates substantial OS
collection overhead but does not measure those individual calls retrospectively
in the official run. The log cannot split its overhead exactly among OS calls,
Windows scheduling/polling and processing. Similar cadence in all phases and
low queues/errors do not support capture overload as the primary cause; flushed
output p95 is only 2.485 ms. Rare console delays are not individually logged.

**Classification: real sensor telemetry scheduling defect.** The validator
correctly counts the emitted records; no evidence supports dropped JSONL health
records or an accounting correction. OS deltas use their actual intervals, so
slower telemetry does not establish lost packet/byte accounting. No Npcap defect,
physical-wire completeness or explanation of the historical abrupt exit is claimed.

### Small fix and verification

In `sensor/capture.py`, retain actual `last_check` for rate denominators and add
an independent deadline anchored to the session monotonic origin. After each
read, advance to the next future whole-second deadline; skip missed deadlines
without fabricating samples. Recovery still creates a new session and baseline;
identity validation, retries, gaps, shutdown, provenance, feature contracts,
queue/flow bounds and all acceptance thresholds are unchanged. Synchronous calls
can still stall; this is not a hard real-time guarantee. See ADR-021.

The new deterministic thirty-minute test with 60 ms collection cost and 2 ms
output cost produced **1,694 samples before the fix** and **1,799 after**.
Additional regressions preserve the 1,699/1,700 boundary, reject 1,669 records
and invalid records, verify actual elapsed-time rates, and ensure a four-second
output stall remains an invalid gap without backfilled samples.
Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`
**89/89 passed in 4.132 seconds**, exit 0. These are offline tests, not new live
acceptance evidence. `git diff --check` passed, exit 0. No new live capture was
started during this investigation; the original evidence file is unchanged.

### Exact next commands and remaining Sprint 1 gates

From repository-root PowerShell, enumerate and verify the intended Ethernet 3
mapping, then start a fresh process using a unique output name. Do not use smoke
or diagnostic duration options; the observer CLI is diagnostic-only.

```powershell
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli capture-interfaces
$acceptanceStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe -u tests/sensor/stability_live.py --interface "Ethernet 3" --process-diagnostics-dir "tmp/sprint1-cadence-$acceptanceStamp-process" | Tee-Object -FilePath "tmp/sprint1-cadence-$acceptanceStamp.jsonl"
$acceptanceExit = $LASTEXITCODE
$acceptanceExit | Set-Content -LiteralPath "tmp/sprint1-cadence-$acceptanceStamp-exit.txt"
$acceptanceExit
```

Keep the laptop awake and adapter connected: first five minutes no intentional
browsing/downloads; minutes five through ten use the automatic controlled HEAD
requests; final twenty minutes normal operation. Preserve summary, exit status
and private process diagnostics. Any real loss, invalid coverage or failed check
prevents acceptance. The prior failed run remains evidence, never relabelled PASS.

After a passing rerun, remaining gates include:

- **Matched live TCP accounting (S1-03):** no matched reference result was found.
  Run `.\.venv\Scripts\python.exe tests/sensor/tcp_reference_live.py --interface "Ethernet 3"`;
  retain/review same-interface/filter/exchange counts and bytes within 5%.
- **Operator idle/memory review (S1-02/S1-05):** labels alone do not prove idle.
  The original low-idle phase has 1,881,611 OS bytes; no arbitrary idle threshold
  is introduced. RSS goes from 79,659,008 to 83,013,632 bytes across health samples
  (about 3.20 MiB growth, with an intervening decline); staying below the limit
  does not resolve memory trend review. Review the rerun trajectory too.
- **Fresh-process live TCP/UDP and start/stop evidence (S1-08):** retain historical
  repeats but validate the changed runner with
  `.\.venv\Scripts\python.exe tests/sensor/manual_live.py --interface "Ethernet 3"`
  in another process. Preserve applicable profile/privacy and manual end-to-end
  stop evidence when recording the final gate decision.
- **Unavailable HTTP sink (S1-05): still mandatory under the written reduced
  scope.** ROADMAP.md retains this row and TESTING_STRATEGY.md explicitly keeps
  it open. No HTTP sink exists; `test_unavailable_backend` raises at preflight
  and cannot prove continuing local output during an HTTP outage. A bounded
  separately authorized sink-independence follow-up is needed; no Django or
  Sprint 2 implementation is started here and no waiver is inferred.
- **Recovery/termination evidence review:** the newer private
  `tmp/stability-process-20260912T090952Z-f0431ad8/` diagnostic reaches 480.125
  seconds with five restarts, 21.251 seconds of gaps, duration stop, successful
  worker/socket cleanup, validator-return and interpreter-atexit markers, empty
  stderr/fault files, and child exit 2. Its observer records `operator_interrupt`
  at approximately 482 seconds, so it is qualified recovery-completion evidence,
  not an untouched observer run or proof of the historical crash's cause. The
  official no-loss run supplies later normal duration completion. Retain both
  when reviewing whether the earlier unexplained termination is sufficiently
  addressed; neither grants uninterrupted acceptance after this cadence fix.

## Scope cleanup and current acceptance summary — 2026-09-11

The final title is **NetSentinel: An Intelligent Real-Time Network Monitoring and Anomaly Detection System**. Four modules remain: Live Network Monitor, Anomaly Detection Engine, Explainable Threat Analysis, and Network Recovery & Demo Lab. Sprint 0 is complete. Sprint 1 implementation is almost complete, but the evidence decision remains **PARTIALLY PASSED / NO-GO for Sprint 2**.

This documentation-only cleanup preserves all existing sensor, recovery, diagnostics, tests, dependencies and the frozen host-v1 contract. Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v` — **86/86 passed in 2.657 seconds**, exit 0. SHA-256 comparison confirms existing non-document files are unchanged; all eight gate rows and host-v1 are unchanged. All 46 local Markdown links resolve; `git diff --check` passed, exit 0 (LF/CRLF notices only). No live capture, hardware probe, backend/dashboard/database or ML implementation was started. Tests establish deterministic behaviour, not hardware acceptance.

All S1-01–S1-08 criteria and numerical thresholds remain unchanged. Historical Phase 1B TCP/UDP capture, exact UDP accounting, flow conservation, feature fixtures and two observed USB recovery events retain their limited evidentiary value. The later termination has no proven cause or confirmed fix. "Almost complete" describes implementation progress, not a Sprint 1 PASS.

| Gate / issue | Remaining evidence |
| --- | --- |
| S1-01 / selected profile | Preserve the recorded hardware/mapping evidence; re-enumerate the actual intended interface before another live run. Today's adapter availability was not measured. |
| S1-02 | A fresh uninterrupted 1,800-second run, at least five minutes idle and five controlled, sustained one-second samples and p95 console delay at most two seconds. |
| S1-03 | Matched live TCP reference on the same interface/filter/time with at most 5% discrepancy, sustained window timing, and repeat controlled TCP/UDP correctness. |
| S1-04 / S1-06 / S1-07 | Previously recorded host-first visibility, privacy inspection and seven-feature definitions/fixtures remain; preserve/recheck applicable runtime evidence. No remote-device/full-network claim. |
| S1-05 | Resolve or collect sufficient evidence about abrupt termination; demonstrate stable completion after recovery separately, then clean sustained RSS/CPU/queues/losses/timing and end-to-end stop within five seconds. Working set remains below 500 MiB. |
| S1-05 optional sink | No HTTP sink exists. The existing unavailable-backend test injects a preflight exception, not an HTTP outage. Keep unavailable-sink independence explicitly unresolved; a bounded authorized follow-up must demonstrate it before claiming this gate. No sink is implemented by this cleanup. |
| S1-08 | Fresh-process live start/stop and controlled observation using recorded steps, then an honest complete gate decision. Gapped/recovered/short diagnostics cannot pass uninterrupted stability. |

### Exact next task

Resume Sprint 1 evidence collection, starting with **read-only interface enumeration** from repository-root PowerShell:

```powershell
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli capture-interfaces
```

After verifying the intended Ethernet 3 alias/GUID is present and capture is locally authorized, repeat the instrumented recovery diagnostic using the existing observer:

```powershell
.\.venv\Scripts\python.exe tests/sensor/stability_observer.py --interface "Ethernet 3" --diagnostic-seconds 480 --recovery-retry-seconds 2 --recovery-timeout-seconds 30
```

Use the original selected adapter; do not silently substitute another interface. If absent, report that blocker and arrange its return before dependent capture. Operator-controlled loss/reconnect is a separate live exercise, not part of this cleanup. Inspect child exit status and terminal lifecycle/summary evidence in the unique ignored directory. The observer itself returns **2 by design** because it is diagnostic-only; read `observer.jsonl` for the child status. A no-loss run does not prove recovery.

After the termination issue is understood or sufficient documented stability evidence supports proceeding, run `tests/sensor/stability_live.py --interface "Ethernet 3"` with **no smoke/diagnostic option** for full 1,800-second acceptance, then the existing matched TCP/manual validators and remaining failure/repeatability checks. Do not combine gapped runs or lower thresholds. Keep sensitive logs private in ignored tmp/.

### Scope and historical evidence

Advanced RBAC, incidents/risk/enterprise alerts/reports, broad inventory/topology, Bluetooth, intelligence/LLM, remote-device monitoring claims, multi-model comparisons, Celery, unjustified microservices and required cloud delivery are **OUT OF SCOPE**. Redis requires a later demonstrated essential need. These removals do not alter proven capture or acceptance evidence.

The earlier sections below are retained in full. Read newest dated evidence first; old "current/final", absent-driver/adapter, untested-recovery and smaller test-count statements apply to their recorded runs only. The historical combined Django/Next.js/roles Sprint 2 recommendation is superseded: after full S1 PASS and explicit authorization, Sprint 2 is simple Django REST/PostgreSQL APIs/persistence with minimal access; Next.js is Sprint 3, Isolation Forest Sprint 4, explanations/labs Sprint 5, and final completion Sprint 6.


## USB recovery observed; unexplained process termination — 2026-09-09

**Current decision: PARTIALLY PASSED / NO-GO. No code-level cause of the abrupt
process termination is proven.** This section supersedes statements below that
hardware recovery has never been demonstrated.

Inspected `tmp/sprint1-usb-recovery-diagnostic-3.jsonl`: Ethernet 3 loss at
133.438 seconds, followed by recovery with a 6.140-second gap. An address/context
change at 141.719 seconds recovered with a second 2.125-second gap. The log has
two `capture_restarted` events and subsequent RUNNING/valid health records.
The operator reports the original GUID returned after USB tethering was toggled;
the implemented identity check permits restart only against the original GUID.
Parser/flow errors, queue drops and overflow remained zero. The final record is
a valid low_idle health sample at 270.016 seconds, UTC
2026-09-09 14:52:28.372932, roughly 126 seconds after the second recovery.
There is no stopped/summary/exception footer. The reported PowerShell exit is
-1; this status is not contained in the captured JSONL itself.

Two other USB logs (`sprint1-usb-recovery-diagnostic.jsonl` and `-2.jsonl`) each
reached 480 seconds and contain normal stopped/summary records, with no loss
events. They are diagnostic evidence, not 30-minute acceptance passes.

**Path analysis:**

- Controlled HTTP traffic starts at 300 seconds. At the last 270-second sample
  that worker should still be waiting; there are no traffic subprocesses in the
  validator. Scapy has optional Windump/helper subprocess utilities, but this
  live path uses an opened Npcap socket, not offline tcpdump processing.
- No `os._exit`, native ExitProcess/TerminateProcess call or `exit(-1)` exists
  in the application path inspected. Its ordinary returns are 0/2. Main-thread
  SystemExit/KeyboardInterrupt can bypass `except Exception`, but normally still
  execute Python finally blocks. Worker SystemExit ordinarily exits that thread,
  not the whole interpreter. Thread exceptions and BaseExceptions were diagnostic
  blind spots; they do not by themselves prove the observed process termination.
- Scapy 2.7.0 stores AsyncSniffer's ordinary exceptions for join; its receive loop
  can close a failed socket. Its L2 pcap socket close is guarded by `closed`.
  The normal sensor path stops/joins before closing and refuses restart after
  failed cleanup. Successful restart therefore supports completed Python cleanup,
  but cannot prove native resource integrity.
- Review risk: the existing cleanup finally calls socket.close even if worker
  join failed, which could be unsafe if a worker remained in a native read.
  No evidence establishes that branch here, and it would block recovery rather
  than produce these successful restarts. No speculative cleanup change was made.
- Native pcap_next_ex/pcap_getevent/pcap_close and Windows API calls remain involved
  after recovery. Adapter recreation/native failure, external forced termination,
  or host/IDE intervention are plausible, unproven explanations. No matching
  Application events 1000/1001/1002 or System critical/error/warning events were
  found for 14:50–14:55 UTC; this does not exclude a native or external failure.

Windows status -1 represents DWORD `0xFFFFFFFF`, not a unique diagnosis and not
the usual access-violation code `0xC0000005`. Exit status may originate from an
explicit exit, external termination or an unhandled native exception; see
[Microsoft GetExitCodeProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess).
Native adapter recreation is a hypothesis, not an established Npcap defect.

**Diagnostics added, not a claimed crash fix:** opt-in fault-handler output,
independent flushed process journal (PID, native thread ID, UTC/elapsed/phase),
uncaught thread/BaseException reporting, validator-return and interpreter-atexit
markers, and before/after socket open, worker readiness, stop/join and close
breadcrumbs. No packet/frame locals, packet repr or native memory dumps are
stored. A separate diagnostic observer launches the same Python validator with
unbuffered stdout/stderr files and records the child status in signed, unsigned
and hexadecimal forms even if Python cleanup does not run. Windows venv launcher
PID and actual interpreter PID can differ; the child journal records its own PID.

**VALIDATION:** 86/86 unit tests passed in 1.609 seconds; seven new tests exercise
process exit observation, thread/BaseException reporting and lifecycle markers.
`git diff --check` passed. An observer CLI check against a deliberately nonexistent
interface retained child exit 2 and validation_error; it opened no capture.
No real USB recovery rerun or native crash was performed during this change.

[Python faulthandler](https://docs.python.org/3.11/library/faulthandler.html) can
report supported fatal faults on Windows. It cannot guarantee evidence for
TerminateProcess, os._exit, power loss or a killed observer. The atexit marker is
evidence that the handler ran, not proof of a successful run or final OS exit.
The parent records its own timeout/operator termination before stopping its
owned child tree, so its intervention is distinguishable. Timeout is diagnostic
duration plus 90 seconds; no acceptance threshold or recovery timeout changes.

Run from repository-root PowerShell (the observer prints a unique ignored tmp/
artifact directory; inspect its files during/after the run):

```powershell
.\.venv\Scripts\python.exe tests/sensor/stability_observer.py --interface "Ethernet 3" --diagnostic-seconds 480 --recovery-retry-seconds 2 --recovery-timeout-seconds 30
```

Artifacts: `stdout.jsonl`, `stderr.txt`, `process.jsonl`, `faults.txt`,
`observer.jsonl`. The observer returns **2** because this is diagnostic-only;
read the **child** exit code in `observer.jsonl`. It changes no adapter, driver,
privileges, firewall or service settings and starts no backend/database/ML.
Repeat the real recovery exercise with this evidence enabled. Preserve the two
observed recovery successes as partial evidence, but stable completion after
recovery is unresolved. Clean 30-minute acceptance remains blocked and must
eventually start from zero without any induced or actual gap.

## Confirmed interface-loss diagnostic and bounded recovery — 2026-09-09

**LATEST VERIFICATION:** 79/79 tests passed in 1.088 seconds. A repeat verification
exposed implicit MAC resolution in the shared Scapy Ethernet fixture; the first
rerun was stopped after resolution attempts and a background-thread exception.
Explicit synthetic source/destination MAC addresses and a no-resolution regression
now keep fixture serialization offline. The subsequent full suite passed without
those warnings/exceptions. This fixes test isolation, not the Wi-Fi disconnection;
the recovery implementation and acceptance requirements remain unchanged.

This section supersedes the earlier unknown-cause diagnosis for the **new
diagnostic run**, not for the historical 367.172-second run. Sprint 1 remains
PARTIALLY PASSED / NO-GO for Sprint 2.

**OBSERVED LOG EVIDENCE:** The local UTF-16 diagnostic log
`tmp/sprint1-wifi-diagnostic-8min.jsonl` contains a complete traceback at
153.079 seconds, phase `low_idle`: `ValueError: Interface 'Wi-Fi' is
down/disconnected`. It follows `stability_live.py:148` -> `capture.py:191` ->
`interfaces.py:34` in the then-current code. The confirmed software trigger is
the OS interface status check reporting Wi-Fi down, not traffic generation,
percentiles or flow parsing. The physical cause (driver, power management,
signal, roaming, etc.) is not established. This plausibly explains the older
ValueError and matches its timing, but the older log cannot prove identical cause.

**IMPLEMENTATION:** A bounded capture supervisor now reports RUNNING,
INTERFACE_LOST, RECOVERING and STOPPED. Known loss uses a typed exception with
an explicit message. Old capture shuts down and flushes partial metadata;
retries revalidate the same alias/GUID and refresh addresses before starting a
new session/queue/counter baseline. Gap time is recorded; no samples or normal
idle windows are fabricated. Defaults: retry every 2 seconds for at most 30
seconds per gap, additionally limited by the finite run deadline. Initial
absence without a trusted GUID fails closed. Timeout ends with
`interface_unavailable`; replacement identity, unrelated exceptions or failed
worker cleanup cannot silently recover. See NETWORK_SENSOR_PLAN.md and ADR-017
for limits, including synchronous OS/output calls.

**DETERMINISTIC COVERAGE:** `test_recovery.py` covers typed loss, same-GUID
recovery, timeout, bounded intervals and duration, refreshed addresses and
counters, incomplete windows/no invented gap samples, valid later idle windows,
replacement GUID rejection, unexpected ValueError propagation, cancellation,
late revalidation and failed cleanup. Stability tests ensure recovered runs
cannot pass clean capture or reset the phase clock; explicitly diagnostic runs
cannot pass acceptance even at 1,800 seconds. No packets are transmitted and
no capture device is opened by these new fixtures.

**FULL TEST RESULT:** 78/78 tests passed in 2.108 seconds with
`.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v`.
This includes 17 new tests relative to the 61-test diagnostic baseline.
`git diff --check` and the validator CLI help check passed. Existing synthetic
IPv6 fixtures emitted route warnings; there were no test failures.

**LIVE LIMITATION:** Recovery has not yet been demonstrated on actual hardware.
Another short diagnostic is recommended; do not alter network configuration
to force a pass. The following automatically stops after eight minutes, keeps
the original phase schedule, and always remains a diagnostic (exit 2 expected):

```powershell
.\.venv\Scripts\python.exe tests/sensor/stability_live.py --interface "Wi-Fi" --diagnostic-seconds 480 --recovery-retry-seconds 2 --recovery-timeout-seconds 30 2>&1 | Tee-Object -FilePath tmp/sprint1-wifi-recovery-diagnostic.jsonl
$LASTEXITCODE
```

Inspect explicit loss/recovery/terminal events. A run with no loss tests normal
operation but cannot prove hardware recovery. No Django, Next.js, PostgreSQL or
ML is started. Existing sensor privacy, caps and all numerical acceptance
thresholds are preserved. Any actual loss disqualifies uninterrupted stability,
even after successful recovery; the full 30-minute acceptance run must still be
rerun from zero in a fresh process without smoke/diagnostic options.

## Wi-Fi failure diagnosis follow-up — 2026-09-09

This follow-up supersedes the earlier descriptions of Wi-Fi as untested for
the **user-reported session only**. Sprint 1 remains PARTIALLY PASSED / NO-GO.

- **USER-REPORTED EVIDENCE:** Wi-Fi captured 111,618 packets / 86,965,322 IP
  bytes and finalized 38 windows over 367.172 seconds. Controlled traffic had
  14 attempts / 14 successes / zero errors. Peak RSS was 86,147,072 bytes;
  parse/flow errors, queue drops and flow overflow were zero. Shutdown took
  approximately 0.016 seconds. Capture stopped with `reason="error"` and
  `ValueError`. Duration, controlled activity, sample coverage and clean capture
  failed; sample/window delay, memory, bounds, conservation and shutdown passed.
- **DIAGNOSIS LIMIT:** No original traceback or message was supplied or found
  in the repository's ignored `tmp/` files. The original harness retained only
  `type(exc).__name__` at `tests/sensor/stability_live.py:109` (before this
  follow-up). This is the exact diagnostic-loss defect, **not an identified
  source of the historical ValueError**. No sensor root-cause fix is claimed.
- **SOURCE ANALYSIS:** The final percentile calculations and acceptance checks
  run after `run_capture` returns and cannot explain its `reason="error"`.
  An exception in the original independent traffic thread does not propagate
  into the capture thread. Interface/address checks, OS counters, clock/window
  advancement, window feature construction and the output callback still need
  the original traceback to distinguish their runtime failure paths. Zero
  parser/flow error counts do not exclude all of these paths.
- **DETERMINISTIC RESULT:** An offline virtual 1,800-second run exercised the
  real capture consumer, counter arithmetic, aggregation and stability callback
  through all three phases without ValueError. Separate virtual controlled
  traffic completed 60 mocked HTTP attempts. No socket/device was opened and
  no request was sent. These tests do not reproduce the historical failure or
  establish live acceptance. Ten read-only OS/interface/resource probes also
  passed; no live capture was started during diagnosis.
- **CHANGE:** The validator now emits exception type, message, full formatted
  traceback without frame locals, phase, elapsed seconds and processing stage.
  It covers preflight, capture/callback errors, worker exceptions and final
  validation/statistics. Unexpected worker errors request bounded shutdown and
  prevent acceptance; expected socket errors remain counted and now carry
  diagnostics. A broken stdout falls back to stderr. Keep exception output
  local in ignored `tmp/`; messages can include private runtime metadata.
- **REGRESSION:** `test_stability_live.py` adds ten offline tests. The diagnostic
  preservation test fails against a temporary reconstruction of the original
  handler because there is no exception record, and passes with the new handler.
  Injected tracebacks were inspected; they are explicitly not the historical
  traceback. No regression for the unknown historical trigger can yet be claimed.
- **FULL SUITE:** `python -m unittest discover -s tests/sensor -v` passed all
  **61 tests in 4.185 seconds** after the change. `git diff --check` passed.
  Scapy emitted route/MAC warnings while constructing existing synthetic fixtures;
  these were not test failures. No web, database or ML service was started.
- **PARTIAL EVIDENCE:** Retain the supplied packet/resource/timing observations
  for that 367-second interval, subject to original-log review. They do not prove
  sustained stability or clean capture. Fourteen successful requests cannot
  satisfy five minutes of controlled activity. Restart the eventual 30-minute
  acceptance run from zero after diagnosis; do not combine sessions.

The original log/traceback is still required to identify and fix the exact
historical trigger. A short instrumentation check, if needed, is:

```powershell
.\.venv\Scripts\python.exe tests/sensor/stability_live.py --interface "Wi-Fi" --smoke-seconds 60 2>&1 | Tee-Object -FilePath tmp/sprint1-wifi-diagnostic.jsonl
$LASTEXITCODE
```

This is not an acceptance rerun, cannot reach the controlled phase, and is
expected to return 2 even without exceptions. It cannot by itself clear the
367-second failure. The full acceptance command remains the same script with
`--interface "Wi-Fi"` and **no smoke option**, after the cause is resolved.
All thresholds, the 1,800-second requirement, sensor bounds, capture source and
privacy handling inside the sensor remain unchanged.

## Current Sprint 1 decision — 2026-09-09 continuation

**PARTIALLY PASSED. NO-GO for starting Sprint 2.** Historical Phase 1B capture
evidence remains valid for its recorded sessions. Today's selected adapter is
absent, so it cannot supply fresh live reference, repeatability or resource
evidence. No alternative interface was selected. All sections below headed Phase
1A/1B are historical; this section and the final decision at the end supersede
their descriptions of current code, hardware state and remaining work.

### Evidence categories and current environment

- **OBSERVED FACT:** Windows 11 Home Single Language 10.0.26200; AMD Ryzen 5
  5600H, 6 cores/12 logical processors, 7,883,554,816 bytes physical RAM.
- **OBSERVED FACT:** Npcap service is Running. Windows `Get-NetAdapter` and fresh
  psutil/Scapy enumeration contain no Ethernet 3/Samsung USB/ifIndex 23 mapping.
  Wi-Fi is Up; this is enumeration only and supplies no packet-capture evidence.
  No interface, routing, firewall or driver configuration was changed.
- **OBSERVED FACT (historical Phase 1B):** Npcap 1.88, AdminOnly=0, Scapy 2.7.0,
  psutil 7.2.2, Python 3.11.0 and driver 2.21.4.0 supported non-elevated real TCP
  and UDP capture on the Samsung adapter. Current dependencies remain unchanged.
- **TEST RESULT:** 51 deterministic unit tests pass; `pip check` passes. Synthetic
  documentation-address packets are constructed/decoded in memory, never sent.
- **ASSUMPTION:** Reconnecting the same adapter may restore its alias/index.
  Re-enumeration must verify this; do not hardcode or assume it.
- **UNTESTED CAPABILITY:** Fresh live operation of the revised instrumentation,
  30-minute stability, matched live TCP reference, live IPv6, Wi-Fi capture,
  hotspot listing/pre-NAT attribution, remote-device visibility and monitor mode.

### Gate-by-gate decision

| Gate | Current result | Exact evidence / remaining requirement |
| --- | --- | --- |
| S1-01 Environment | Passed for recorded Ethernet 3 profile | Actual hardware/runtime/driver/access and mapping recorded in Phase 1B; current absence disclosed |
| S1-02 Independent visible operation | Not fully passed | Prior local counters/capture succeeded without backend/model; 30-minute staged run and sustained p95 console latency not measured |
| S1-03 Packet/window correctness | Not fully passed | Prior two-direction TCP/UDP and 10-second windows; exact UDP reference and deterministic fixtures pass. Matched TCP reference and sustained window latency remain unmeasured |
| S1-04 Visibility/attribution | Passed for host-first scope | Capability matrix below; experimental hardware capabilities are excluded, not inferred |
| S1-05 Failure/resource bounds | Not fully passed | Injected failures/caps/drop accounting pass. Actual 30-minute RSS/CPU/bounds/output, end-to-end shutdown remain unmeasured; optional HTTP sink does not exist, so unavailable-sink integration remains untested |
| S1-06 Privacy/scope | Passed for inspected source and produced evidence | Whitelisted bounded metadata, no payload persistence/output, no scan/block/elevation; revised code has no successful live-run output yet |
| S1-07 Frozen contract | Passed for minimum definitions and deterministic fixtures | Seven fields frozen in LIVE_FEATURE_CONTRACT.md and implemented from retained flow statistics; no additional dataset-only features |
| S1-08 Repeatability/decision | Not fully passed | Prior Phase 1B fresh-process success retained; today's fresh counters/capture/controlled repeat cannot start on missing adapter. Conservative decision recorded |

### Implementation and deterministic results

`run_capture` now emits one-second health records with real OS totals/deltas,
monotonic elapsed interval, UTC sample end, CPU percentage (psutil process scale),
RSS, Windows peak working set, queue/flow/window depth and high-water marks,
normalization/parser/flow error counts and application drops. Stop records include
final RSS, peak RSS, queue remainder and cleanup seconds. An optional local
threading event requests shutdown; Ctrl+C remains supported. No remote control
or HTTP sink was added. Health sampling is in the local capture consumer; slow
output can delay it and must be measured, not claimed independent of output.

Features are reconstructed from each finalized window plus its retained selected
local-address context. Unknown/incomplete windows emit null features. A late drop
now conservatively marks subsequent session windows partial, matching existing
queue/parser-loss policy; already finalized windows are not rewritten. Tests
were adjusted to this explicit loss policy, not to change reference tolerances.

**TEST RESULT: 51/51**, including the original 32 plus 19 new tests: seven-feature
hand arithmetic, idle, half-open boundaries, missing headers, shutdown/context,
peer deduplication, independent reference parser, wrap invalidation, full 20,000
queue pressure (20,007 puts -> 20,000 retained / 7 counted drops), late-loss
propagation, malformed length, unavailable backend, adapter disappearance,
worker disappearance, counted parser/flow failures, wall-clock jump, requested stop
and genuinely empty running capture. Existing tests also exercise the flow cap,
permission denial, Ctrl+C, bounded worker join, IPv6 extensions/fragments and
clock-gap handling. Fault injection is unit-level evidence, not a claim of
physically unplugging hardware or resuming Windows from sleep during capture.

### Authoritative 30-minute run — PREPARED, NOT COMPLETED

There is **no 30-minute stability result**, no measured live peak/final RSS and no
sustained p95 latency from this continuation. `stability_live.py` failed before
capture because selected-interface IPv4 was unavailable. No duration was shortened
and presented as passing. The 500 MiB limit remains unchanged.

After reconnecting the adapter, use repository-root PowerShell:

```powershell
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli capture-interfaces
.\.venv\Scripts\python.exe -m sensor.cli counters --interface "Ethernet 3" --samples 5
.\.venv\Scripts\python.exe -m sensor.cli capture --interface "Ethernet 3" --duration 10
.\.venv\Scripts\python.exe tests/sensor/stability_live.py --interface "Ethernet 3" --smoke-seconds 10
New-Item -ItemType Directory -Force -Path tmp | Out-Null
.\.venv\Scripts\python.exe tests/sensor/stability_live.py --interface "Ethernet 3" | Tee-Object -FilePath tmp/sprint1-stability.jsonl
```

The smoke option is instrumentation-only and intentionally cannot return a full
stability PASS. For the full command, keep the laptop awake and adapter attached.
First **300 seconds: low/idle** (avoid intentional browsing/downloads). Next
**300 seconds: automatic controlled ordinary traffic**, one public HTTP HEAD
to 1.1.1.1:80 approximately every five seconds, bound to the selected local IPv4.
Final **1,200 seconds: normal operation**. HTTP reply contents exist transiently
only to check success and are never printed/stored. No user action is required
to trigger the controlled phase. Ambient traffic is still captured and counted.

The script prints and flushes metadata-only health JSON to the console and
optionally `Tee-Object` records it in ignored `tmp/`. It suppresses endpoint-level
flow details, counts all window packets/bytes and emits a final summary. Inspect
the PowerShell `$LASTEXITCODE` immediately after the command and retain the summary.
It records RSS over time, actual Windows peak working set, final RSS, CPU, queue
and flow bounds/drops, parse/flow errors, interval timing, p95 sample-end-through-
flushed-print latency, p95 window processing after end+2 seconds, and shutdown
cleanup/duration overrun. It does not measure physical screen rendering.

Automated checks require 1,800 seconds, >=1,700 valid samples, p95 console delay
<=2 seconds, p95 window processing after lateness <=1 second, peak RSS <500 MiB,
caps <=20,000/10,000/2, conservation, no errors/crash and shutdown <=5 seconds.
The >=55 successful HEAD requests and sample-count threshold are **validator
coverage assumptions**, not revised roadmap tolerances. Any nonzero loss needs
review even though pressure-test counted drops are expected. Do not rerun merely
to hide inconvenient measurements. Windows kernel loss remains unknown.

An automated-check success is only a candidate: review the entire RSS trajectory
for unexplained persistent growth, the first five minutes' actual activity and
the controlled-phase results. The script explicitly requires operator idle-phase
and memory-trend review. Record peak/final RSS, phase sample counts/rates, min/max
and p95 timing, and any loss/error explanations before accepting S1-02/S1-05.
No arbitrary low-traffic byte threshold is invented. Steady growth below 500 MiB
still needs explanation. The collector/history is bounded for this finite run.

For a separate real Ctrl+C check run `capture --interface "Ethernet 3" --duration
60`, press Ctrl+C while idle, and time to prompt return; retain capture_stopped.
The emitted cleanup time excludes delay before handling the interrupt and final
stdout flush; end-to-end prompt return must also be <=5 seconds. Blocked stdout
is not guaranteed bounded. Do not use force termination as a graceful-stop result.

### Matched TCP reference — PREPARED, NO LIVE RESULT

```powershell
.\.venv\Scripts\python.exe tests/sensor/tcp_reference_live.py --interface "Ethernet 3" | Tee-Object -FilePath tmp/sprint1-tcp-reference.json
.\.venv\Scripts\python.exe tests/sensor/manual_live.py --interface "Ethernet 3"
```

The reference validator opens a second non-promiscuous Npcap socket on the same
resolved device, filtered to the reserved ephemeral TCP port and 1.1.1.1:80. The
reference is ready before the sensor starts traffic. The laptop sends one HTTP
HEAD after the sensor signals readiness; both readers include the exchange and
teardown. Unused margins contain no other traffic on the exact reserved tuple.
The reference parses Ethernet/IPv4 lengths and TCP coordinates independently via
`struct`, without the sensor normalizer/aggregator, retaining only six counters.
Unsupported/truncated/VLAN/fragment records fail reference validation explicitly.
It is independent accounting on the same observation point, **not independent
wire capture**: shared driver/offload/kernel-loss blind spots remain.

Output contains captured/reference total and directional packet/IP-byte counts,
signed differences, absolute discrepancy percentages and pass checks using the
unchanged **5% maximum**. All directional denominators must be nonzero and HTTP
success/clean sensor/reference state are required. Investigate timing/filter,
offload and loss discrepancies; do not assume a TCP packet count from application
bytes, or alter the tolerance to pass.

| TCP accounting field | Current result |
| --- | --- |
| Captured packet count / bytes | Not measured this continuation |
| Matched reference packets / bytes | Not measured; adapter absent |
| Discrepancy / explanation | Undefined, not 0%; no exchange attempted |
| Prior Phase 1B observation | 11 packets / 747 IP bytes; not an independent TCP reference |
| Deterministic reference parser | Exact 40-byte IPv4 TCP fixture passes; truncated frame rejected |

### Capability matrix

Statuses describe the recorded observation profile, not present connectivity.
SUPPORTED means demonstrated within the stated scope; UNTESTED means no hardware
validation. Experimental capabilities below are deferred research scope.

| Capability | Status | Evidence |
| --- | --- | --- |
| Interface enumeration/counters | SUPPORTED | Prior live samples; fresh enumeration works; selected adapter currently absent |
| Real packet capture | SUPPORTED | Historical non-elevated Ethernet 3 Phase 1B sessions |
| IPv4 | SUPPORTED | Controlled historical TCP/UDP addresses and IP lengths |
| IPv6 live capture correctness | UNTESTED | Local addresses/parser fixtures alone do not validate live exchange |
| TCP | SUPPORTED | Prior bidirectional exchange; matched reference still pending |
| UDP | SUPPORTED | Prior exact one-query/one-response DNS length/count reference |
| Flow aggregation | SUPPORTED | Historical captured/aggregated conservation, boundary evidence and exact fixtures |
| Direction inference | SUPPORTED | Selected-address membership and prior bidirectional laptop exchange; unknown stays unknown |
| Laptop traffic on Ethernet 3 | SUPPORTED | Prior own-host sockets explicitly bound to that adapter |
| Observed remote IP endpoints | SUPPORTED | Controlled public peer endpoints; not LAN-device discovery |
| Wi-Fi capture | UNTESTED | Currently Up only; no capture attempted |
| Hotspot client listing | EXPERIMENTAL | No Windows client-list experiment |
| Hotspot pre-NAT attribution | EXPERIMENTAL | No known-client traffic mapping |
| Other remote-device traffic visibility | EXPERIMENTAL | No controlled remote-device visibility evidence |
| Monitor mode | EXPERIMENTAL | Not attempted; prior Dot11Support=0; hardware feasibility unknown |
| IPv6 jumbograms / IP reassembly | UNSUPPORTED | Explicit normalizer limitation; no reassembly state |

### Privacy recheck and fresh-process repeatability

**TEST RESULT / SOURCE INSPECTION:** Production capture remains `store=False`,
`promisc=False`, one explicit interface, IP filter and metadata-only bounded queue.
No packet-file writer, payload output, scanning, firewall/blocking action, shell
elevation or driver installer exists. Parser exceptions retain only counters;
payload-exclusion tests pass. Reference packets are transient and never retained.
All network sends occur only in explicitly invoked benign validation scripts,
never in unit tests or ordinary sensor capture. CLI flow output includes private
endpoint/local-address metadata; do not commit it. No new capture/log/data/model
artifact was created by the attempted live commands. Existing ignored Phase 1B
metadata remains historical; it was not replaced or promoted to today's evidence.

Fresh separate processes actually run on 2026-09-09:

| Exact command (prefix `.\.venv\Scripts\python.exe`) | Result |
| --- | --- |
| `-m sensor.cli interfaces` | Exit 0, current interfaces listed; Ethernet 3 absent |
| `-m sensor.cli capture-interfaces` | Exit 0, Npcap mappings listed; Ethernet 3 absent |
| `-m sensor.cli counters --interface "Ethernet 3" --samples 5` | Explicit unavailable-interface error; no samples |
| `-m sensor.cli capture --interface "Ethernet 3" --duration 10` | Explicit unavailable-interface error; no capture/windows |
| `tests/sensor/stability_live.py --interface "Ethernet 3" --smoke-seconds 5` | Exit 2, selected-interface IPv4 unavailable; no run |
| `tests/sensor/tcp_reference_live.py --interface "Ethernet 3"` | Exit 2 after error-output hardening, reference_error; no exchange |
| `tests/sensor/manual_live.py --interface "Ethernet 3"` | Exit 1, selected-interface IPv4 required; no exchange |
| `-m unittest discover -s tests/sensor -q` | 51 tests, OK |
| `-m pip check` | Exit 0, no broken requirements |

Expected missing-driver and stop messages in unit output are injected test paths,
not evidence that the installed Npcap driver is absent. No hardware failure was
fabricated. The actual absent adapter blocks additional live work.

## Current decision: Phase 1B real capture demonstrated

Updated 2026-09-08. **Sprint 1: PARTIALLY PASSED. Phase 1B real-packet objective: PASSED on Ethernet 3.** Real, controlled bidirectional TCP and UDP were observed on a non-loopback interface and passed through the bounded ten-second aggregator. Missing Npcap is no longer a blocker. This does not complete the roadmap's full S1-01 through S1-08 gates or prove Wi-Fi capture. Historical Phase 1A results below remain an audit trail, not the current driver state.

### Npcap, environment and interface mapping

Windows remains Windows 11 Home Single Language 10.0.26200, AMD64; project Python remains 3.11.0, psutil 7.2.2. Scapy was absent, then installed **only inside the existing .venv**, version **2.7.0**, now pinned. No PyShark/TShark, system pip installation or driver/configuration change was performed.

Npcap was manually installed by the operator. Current evidence:

- `Get-Service npcap`: **Running**, start type **System**.
- Driver `npcap.sys` and `NPFInstall.exe`: file/product version **1.88**.
- Scapy-loaded `pcap_lib_version()`: **Npcap version 1.88, based on libpcap version 1.10.6 (64-bit time_t)**. The wpcap DLL file version 1.10.6 is the underlying libpcap version, not the Npcap installer version.
- Registry Parameters: `AdminOnly=0`, `Dot11Support=0`, `LoopbackSupport=1`, `DltNull=1`, `WinPcapCompatible=1`, `VlanSupport=0`. No options were changed. Raw 802.11 support is not enabled; monitor mode was not attempted. [Npcap documents these registry options and runtime version checks](https://npcap.com/guide/npcap-devguide.html).
- `IsUserAnAdmin()` returned False. Real captures succeeded from this same non-elevated process without a UAC prompt. This proves access for this user/configuration only; permission-denied behavior is unit fault-injected, not tested by changing driver permissions. [AdminOnly behavior is documented by Npcap](https://npcap.com/guide/npcap-users-guide.html).

Fresh Windows and Scapy enumeration agree on **Ethernet 3**, **ifIndex 23**, SAMSUNG Mobile USB Remote NDIS Network Device #2, driver 2.21.4.0, status Up. Exact selected capture identifier:

```text
\Device\NPF_{F6428BE8-4357-41F9-A78D-5909098A0567}
```

Windows InterfaceGuid matches the brace-delimited capture GUID. The active IPv4/default route is still on this USB interface; IPv6 addresses also exist. Addresses are taken freshly from the selected interface and include IPv6 (zone suffix removed for comparison); they are not inferred from a peer or gateway. Exact private addresses are in ignored local evidence rather than a committed inventory.

Scapy exposed 13 interface mappings: Ethernet 3; disconnected Wi-Fi, Ethernet, Bluetooth, TAP/NordLynx/OpenVPN and two Wi-Fi Direct adapters; loopback; and three WAN miniports. Windows additionally exposes non-capture/hidden components. Enumeration alone does not imply any of them supports traffic capture. Wi-Fi remains disconnected and was not silently enabled or substituted for the USB path.

An initial `socket.if_nametoindex('Ethernet 3')` attempt failed because Winsock expects its internal interface name on this machine. Inspection of `socket.if_nameindex()` confirmed internal names. Implementation now uses Windows `ConvertInterfaceAliasToLuid` / `ConvertInterfaceLuidToIndex`, then requires a unique matching Scapy index/name and Npcap identifier. Capture succeeded after this correction. No hardcoded Ethernet 3 GUID exists in sensor code.

### Real TCP, UDP and aggregation evidence

The CLI smoke test `capture --interface 'Ethernet 3' --duration 2` exited 0, with 91 IP packets represented in partial shutdown flow summaries. Ambient traffic is only smoke evidence, not the controlled result below.

Controlled validation binds sockets to the selected laptop IPv4 address. No scans, flooding, unsolicited LAN connections, Wi-Fi/hotspot changes, routing changes or firewall changes occur. It sends one public HTTP HEAD to **1.1.1.1:80** and one standard recursive DNS A query for **example.com** to **1.1.1.1:53**. Only socket coordinates, success booleans, message lengths and captured metadata aggregates are output; HTTP/DNS response bodies are not retained in files.

An earlier HTTPS test to 1.1.1.1:443 with SNI one.one.one.one failed with **SSLCertVerificationError**. Its TCP handshake/TLS exchange was visible (16 packets / 3,845 IP bytes), but no successful HTTPS response is claimed. Certificate verification was not disabled; root stores and network interception settings were not changed or diagnosed. The harmless HTTP test replaces this test dependency, not a security setting of the sensor.

| Evidence | Successful 24-second run | Fresh-process repeat |
| --- | --- | --- |
| Session | 2eadfde9-7acc-4e2e-b86d-5de1c590250e | ee70fbd5-3416-44a1-901c-f2bdfcdb4d47 |
| Capture start, UTC epoch seconds | 1788889328.970552 | 1788889389.797335 |
| Total invocation wall time | 24.562 s | 24.547 s |
| HTTP response received | Yes, begins HTTP/ | Yes, begins HTTP/ |
| Controlled local TCP port | 57220 | 56708 |
| TCP to/from 1.1.1.1:80 | 11 packets / 747 IP bytes | 11 packets / 747 IP bytes across two windows |
| TCP outbound / inbound | 6 / 5 packets, 313 / 434 bytes | 6 / 5 packets, 313 / 434 bytes |
| TCP observed IP lengths | 40–262 bytes | 40–262 bytes |
| Controlled local UDP port | 57420 | 53952 |
| DNS request / response | 1 / 1 packets, 57 / 89 IP bytes | 1 / 1 packets, 57 / 89 IP bytes |
| DNS response validation | Matching peer/transaction, response bit, rcode 0 | Same checks passed |
| All captured/aggregated IP packets | 1,909 / 1,909 | 1,762 / 1,762 |
| All aggregated IP bytes | 616,885 | 344,850 |
| Windows emitted | 4, including startup/shutdown partials | 4, including startup/shutdown partials |
| Parser errors, queue drops, late packets, flow overflow | All 0 | All 0 |
| Queue left at stop / shutdown error | 0 / False | 0 / False |

All captured flow counts sum to the normalizer counts; the repeat script explicitly checks this conservation. DNS application lengths were 29 and 61 bytes, so the independent socket observation predicts 29+20+8=57 and 61+20+8=89 IPv4 bytes. Observed packet counts and lengths matched exactly. TCP endpoints/ports, bidirectional counts, packet length ranges and first/last packet timestamps were present. These are IP lengths, not wire lengths or application byte totals.

Real boundary evidence in the repeat: the same TCP tuple had 9 packets / 667 bytes in [1788889380,1788889390), then 2 packets / 80 bytes in [1788889390,1788889400). The first segment's last timestamp was 1788889389.852911; the second segment began 1788889390.153559. No packet objects were retained to obtain these segments.

The repeat finalized three closed windows at end+2 seconds plus approximately 12, 7 and 18 ms respectively (processing timestamps within approximately 37 ms of end+2). These short observations are not a sustained p95 latency benchmark. Startup and shutdown windows are partial. Some other windows are partial from conservative incomplete/unknown-direction protocol handling; partial=False means no known application-level incompleteness, not proof of zero kernel loss. Kernel drop statistics remain **unknown**.

Private, metadata-only local evidence files (ignored by Git): `tmp/sprint1b-controlled.json` (initial TLS failure), `tmp/sprint1b-controlled-http.json` (HTTP success), `tmp/sprint1b-repeat.json` (fresh-process success). The manual validator filters flow rows to the controlled socket tuples; an empty flow list in these filtered records is **not an idle-traffic claim**. All-flow totals include ambient packets. The final validator explicitly labels this filter and counts omitted flows for future runs; the recorded earlier outputs predate that presentation label. No PCAP or payload dump was created.

### Implementation, tests and commands

Changed `sensor/capture.py`, `sensor/cli.py`, `sensor/flows.py`, `sensor/__init__.py` and `requirements-sensor.txt`; added `sensor/normalize.py`, `tests/sensor/test_capture.py` and explicitly invoked `tests/sensor/manual_live.py`. Updated README, architecture ADR-015, sensor plan, roadmap status and testing strategy. Existing 14 tests were preserved unchanged.

The source opens one Scapy L2listen socket with `promisc=False` and BPF `ip or ip6`. AsyncSniffer uses **store=False**, no offline file and no reassembly session. Its callback extracts only whitelisted outer-IP metadata and enqueues it. A bounded consumer advances the existing aggregator every approximately 50 ms, independently of packet arrivals. IP payload bytes may exist transiently in driver/parser memory; they are never a retained metadata field, logged, dumped or written to a capture file. [Scapy documents store=False and asynchronous lifecycle](https://scapy.readthedocs.io/en/stable/api/scapy.sendrecv.html).

Bounds remain 20,000 queued metadata records and 10,000 active flow entries. Queue drops/parser failures conservatively mark all remaining session windows partial. No spool or database exists. The worker stop uses a two-second join; duration expiry worked in real runs and Ctrl+C cleanup is unit fault-injected. Blocked stdout and sustained overload remain unmeasured; a bounded join is not an end-to-end shutdown timing guarantee under arbitrary output blockage.

**32 unit tests passed**, including all original 14. Added IPv4 TCP, UDP, IPv6 extension headers, fragments/truncation, non-IP handling, outer ICMP versus embedded TCP, payload exclusion, live-provenance conversion-to-flow boundaries, loss flags, invalid/loopback interfaces, duration limits, permission faults, bounded join, idle duration stop, Ctrl+C socket cleanup, administrator-only refusal without elevation, and fail-closed unknown driver access options. Mock capture lifecycle tests also feed decoded packets through the actual normalizer, queue and aggregator; they make no network transmissions. `pip check` passed; `git diff --check` passed (Git emits expected Windows line-ending notices).

After adding the explicit AdminOnly preflight guard, a final one-second CLI smoke capture exited 0 with 33 normalized packets, zero parser/queue/late/overflow errors and clean shutdown. The guard reads driver options before opening the socket; it refuses non-elevated AdminOnly capture rather than allowing NpcapHelper to request elevation. Driver options were not changed. The complete 32-test suite passed on this final capture implementation.

Commands executed in addition to Phase 1A reads:

```powershell
git status --short
rg --files -g AGENTS.md
Get-CimInstance Win32_OperatingSystem
Get-Service npcap
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\npcap\Parameters'
Get-NetAdapter -IncludeHidden
Get-NetIPAddress
Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0'
Get-Item 'C:\Program Files\Npcap\NPFInstall.exe',C:\Windows\System32\drivers\npcap.sys
.\.venv\Scripts\python.exe -m pip show scapy psutil
.\.venv\Scripts\python.exe -m pip install scapy
.\.venv\Scripts\python.exe -m sensor.cli capture --interface 'Ethernet 3' --duration 2
.\.venv\Scripts\python.exe -m sensor.cli capture --interface 'Ethernet 3' --duration 1
.\.venv\Scripts\python.exe -m sensor.cli capture-interfaces
.\.venv\Scripts\python.exe -m sensor.cli capture --interface 'does-not-exist' --duration 1
.\.venv\Scripts\python.exe -m sensor.cli capture --interface 'Loopback Pseudo-Interface 1' --duration 1
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v
.\.venv\Scripts\python.exe tests/sensor/manual_live.py --interface 'Ethernet 3'
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Python introspection additionally checked platform/version/elevation, `conf.ifaces`, `pcap_lib_version`, `socket.if_nameindex` and Scapy's lifecycle implementation. Capture-interface and invalid-interface CLI checks are read-only except for the explicitly requested capture socket. Invalid-interface and loopback commands returned exit 2 with clear errors before opening capture. The manual validation was run once with HTTPS (failed application validation), then twice with HTTP (both exit 0); durations and implementation refinements are disclosed above.

### Visibility boundary and remaining gates

**Proven:** metadata of controlled own-laptop IPv4 TCP and UDP crossing the selected USB adapter, both directions, bounded flow aggregation and repeat local duration shutdown. Direction is address-membership evidence at that interface, not proof that all forwarded traffic belongs to the laptop.

**Not proven:** controlled real IPv6 exchanges (unit extraction only), Wi-Fi capture, other devices' traffic, hotspot client listing or pre-NAT attribution, monitor mode, full LAN visibility, attack detection or packet-loss-free physical wire accounting. ICMP identifiers, IPv6 jumbograms and reassembly are unsupported; such metadata is rejected or marked incomplete. No traffic was classified as malicious.

| Roadmap gate | Current status / remainder |
| --- | --- |
| S1-01 | Environment, driver and selected OS/capture mapping recorded; sustained resource profile remains |
| S1-02 | Independent counters/capture run; required 30-minute idle/controlled run and counter latency benchmark outstanding |
| S1-03 | Phase 1B real bidirectional TCP/UDP and window objective passed; full gate remains partial pending matched TCP reference comparison/offload accounting and sustained finalization latency evidence |
| S1-04 | USB own-host boundary recorded; Wi-Fi/hotspot/monitor/remote attribution untested, no inferred support |
| S1-05 | Unit bounds/fault cleanup and real duration stop demonstrated; memory/CPU, pressure integration, sleep/resume, blocked output and full shutdown benchmark outstanding |
| S1-06 | One selected local scope, no payload files/scans/configuration changes; live output contains sensitive metadata and stays local |
| S1-07 | Minimum feature contract not frozen or implemented; no model work |
| S1-08 | Fresh-process controlled observation repeated; complete sprint pass/no-go awaits remaining gates |

**Remaining blocker to packet feasibility: none on Ethernet 3. Overall Sprint 1 remains PARTIALLY PASSED.** If the required final capture point is Wi-Fi, its disconnected state means that separate hardware gate remains untested. The TLS certificate issue is recorded but does not prevent controlled TCP capture via the successful harmless connection.

**Exact recommended next action:** authorize the remaining Sprint 1 acceptance work on the proven USB interface: a measured 30-minute run including five minutes idle and five minutes controlled traffic, matched TCP reference accounting, memory/CPU/latency/loss and failure evidence, and the minimum feature contract. Re-evaluate Wi-Fi separately when that intended interface is connected by the operator. Do not begin Sprint 2 automatically.

## Historical Phase 1A evidence

Inspection date: 2026-09-08. **Overall Sprint 1: BLOCKED at the packet gate.** Phase 1A counters and pure aggregation passed their limited checks. Real capture was not attempted. No claim of complete Sprint 1, traffic attribution, capture accuracy or ML capability follows from these results.

## Detected environment

- Windows 11 Home Single Language, version 10.0.26200, build 26200, 64-bit.
- AMD Ryzen 5 5600H with Radeon Graphics: 6 cores / 12 logical processors; 7,883,554,816 bytes physical RAM (approximately 7.34 GiB).
- Python launcher lists only Python 3.11.0, AMD64, per-user Python311 installation. Project `.venv` created from it.
- Initially psutil, Scapy and PyShark were not detected in that interpreter. Installed psutil 7.2.2 into `.venv` only, pinned in requirements-sensor.txt. Scapy and PyShark remain uninstalled; no TShark dependency is introduced.
- Npcap service/registry/install directory, standard wpcap DLL and driver file were not found. This is absence evidence at standard locations, not an exhaustive disk search. No driver was installed.
- Current process has medium integrity; Administrators membership is deny-only (not elevated). Interface enumeration and counters worked without elevation. Driver installation requires manual administrator setup. Whether subsequent capture needs elevation depends on Npcap access options and must be tested; it is not proven here. See [Npcap user guide](https://npcap.com/guide/npcap-users-guide.html) and [Scapy Windows installation](https://scapy.readthedocs.io/en/stable/installation.html).

Exact local addresses and gateway are kept only in ignored `tmp/sprint1-local-ipv4.json` and `tmp/sprint1-local-route.json`, avoiding a committed personal network inventory. Console enumeration displays real addresses. The selected interface had a non-link-local private IPv4 /24 and the only discovered IPv4 default route, metric 0. Other disconnected adapters mostly had link-local /16 addresses; NordLynx also retained a private address. An assigned address does not imply an active link.

## Adapter observations

| Adapter | State / driver | Interpretation |
| --- | --- | --- |
| Ethernet 3, ifIndex 23 | Up; SAMSUNG Mobile USB Remote NDIS Network Device #2; 2.21.4.0 | Selected for counters and further packet feasibility; USB network path, not proof of Wi-Fi capture |
| Wi-Fi, ifIndex 15 | Disconnected; MediaTek Wi-Fi 6E MT7922 (RZ616) 160MHz PCIe Adapter; 3.4.0.1046 | Cannot validate intended Wi-Fi capture in current state |
| Ethernet, ifIndex 5 | Disconnected; Realtek Gaming GbE Family Controller; 1168.19.704.2024 | Not currently usable |
| NordLynx | Disconnected; 0.10.0.0 | VPN; no visibility inferred |
| Local Area Connection 2 | Disconnected; TAP-NordVPN Windows Adapter V9; 9.27.0.0 | VPN |
| OpenVPN Data Channel Offload for NordVPN | Disconnected; 1.3.3.0 | VPN |
| Bluetooth Network Connection | Disconnected; 10.0.26100.8972 | Untested |
| Local Area Connection* 1 and * 2 | Disconnected; Microsoft Wi-Fi Direct Virtual Adapters; 10.0.26100.8972 | Does not establish hotspot support |
| WAN Miniports | IP, IPv6, Network Monitor report Up; SSTP, IKEv2, L2TP, PPTP, PPPOE disconnected; 10.0.26100.1 | Hidden OS components; not selected capture interfaces |
| Kernel Debug Network Adapter | Not Present; 10.0.26100.8521 | Not usable |
| Teredo, IP-HTTPS, 6to4 | Not Present | Not usable |
| Loopback Pseudo-Interface 1 | Up; IPv4 loopback | Excluded from intended packet gate |

psutil enumerated ten interfaces including loopback. Windows `Get-NetAdapter -IncludeHidden` also listed hidden components. Candidate means up with a non-loopback, non-link-local IPv4 address, not proven capturability. Capture GUID mapping is still unknown.

## Commands and results

Read AGENTS.md, README, product requirements, architecture/review, roadmap, sensor plan, ML methodology, security rules, testing strategy and API plan before implementation. `git status --short` initially returned clean; `rg --files` found only the root AGENTS.md.

Read-only environment commands:

```powershell
Get-CimInstance Win32_OperatingSystem
Get-CimInstance Win32_Processor
Get-CimInstance Win32_ComputerSystem
py -0p
python --version
Get-NetAdapter -IncludeHidden
Get-NetIPAddress -AddressFamily IPv4
Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0'
Get-Service npcap,npcap_wifi,npf -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\SOFTWARE\Npcap','HKLM:\SOFTWARE\WOW6432Node\Npcap','HKLM:\SYSTEM\CurrentControlSet\Services\npcap' -ErrorAction SilentlyContinue
Test-Path C:\Windows\System32\Npcap\wpcap.dll
Get-Item C:\Windows\System32\drivers\npcap.sys,'C:\Program Files\Npcap' -ErrorAction SilentlyContinue
whoami /groups
```

Python `importlib.metadata` checked psutil/scapy/pyshark; `sys.executable` and `platform.machine()` checked interpreter/architecture. Initial mixed PowerShell table formatting hid some fields; reran with explicit JSON/table formatting. Missing registry/service/path lookups produced no records, and DLL check returned False.

Setup and verification executed:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install psutil
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli counters --interface 'Ethernet 3' --samples 5
.\.venv\Scripts\python.exe -m sensor.cli capture --interface 'Ethernet 3'
.\.venv\Scripts\python.exe -m sensor.cli counters --interface 'does-not-exist' --samples 1
```

pip installed its cached Windows AMD64 wheel successfully; `pip check` found no broken requirements. **14 unit tests passed**. Tests cover rates, reset/recovery, invalid elapsed time/gaps, bidirectional keys, direction, exact hand-computed totals, ten-second boundary, two-second lateness, idle timer finalization, flow cap, counted oldest queue drops, shutdown/clock-gap rejection, missing headers, IPv6 normalization, invalid provenance, injected Ctrl+C and missing-driver preflight. Ctrl+C was fault-injected, not a measured physical console interrupt. Missing-interface and capture-preflight commands returned exit 2 as intended. Preflight opened no socket.

Five real samples on Ethernet 3, 17:26:43–17:26:47 UTC:

| Sample | Elapsed seconds | Sent bytes | Received bytes | Sent packets | Received packets |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.031 | 586 | 6757 | 6 | 31 |
| 2 | 1.032 | 860 | 2937 | 7 | 20 |
| 3 | 1.031 | 3374 | 4058 | 18 | 24 |
| 4 | 1.031 | 4276 | 5655 | 19 | 30 |
| 5 | 1.031 | 2598 | 4027 | 15 | 29 |

These are interval deltas from actual OS counters; upload/download are bytes divided by measured monotonic seconds (first sample approximately 568.38 / 6553.83 B/s). Approximately one-second scheduling is observed, not an exact real-time guarantee. Traffic was ambient, not a controlled TCP/UDP exchange. No packets or protocol attribution can be inferred from these counts. [psutil counter semantics](https://psutil.io/api/) distinguish cumulative OS measurements; nowrap=False permits explicit reset detection.

## Implemented contract and bounds

Runtime files: sensor/__init__.py, interfaces.py, counters.py, models.py, flows.py, capture.py, cli.py; requirements-sensor.txt and tests/sensor/test_foundation.py. README, architecture decision ADR-014, roadmap evidence link and sensor-plan status updated. `.venv` and the local address appendix are ignored, not committed.

- Counter records: LIVE, local session UUID, UTC observation time, explicit OS_COUNTERS/OS_COUNTERS_ONLY, four cumulative totals and interval deltas, upload/download B/s. Negative deltas invalidate the interval and reset the session. Sampling gaps over three seconds, address/state changes and wall/monotonic divergence invalidate rather than invent rates. Three seconds and one second divergence are provisional feasibility thresholds.
- Metadata whitelist: UTC epoch timestamp, interface, canonical IP addresses, nullable ports, protocol, observed IP byte length, conservative direction, incomplete flag and optional SYN flag. No raw packet, payload, DNS or MAC storage. Actual packet normalization is deferred.
- Canonical bidirectional endpoint key includes interface and protocol, nested within immutable-purpose session/mode windows. Direction uses selected-interface address membership only; both/neither local is unknown. Null transport headers mark incomplete. ICMP currently groups by IP/protocol with null ports; protocol-specific identifiers await capture implementation.
- Half-open [start,start+10) epoch-aligned windows, finalized by explicit watermark at end+2; late packets counted and rejected. At most two open windows and 10,000 flow entries across them. Overflow rejects new keys, preserves existing keys and marks partial. Metadata queue caps at 20,000, drops oldest and counts losses. No persistent spool or output history.
- Pure fixture: outgoing TCP 60 bytes, incoming TCP 100 bytes, outgoing UDP 40 bytes = 3 packets / 200 IP bytes / 2 flow keys. Stored directional totals and SYN count are hand-verified. Fixture uses documentation IPs, SIMULATION provenance and no network transmissions.
- Clock reversals or watermark jumps over 30 seconds fail explicitly; caller must partial-flush and begin a new session. Startup fragment and shutdown windows are partial. Idle windows require the caller to attest ongoing observation; no live runner currently makes that assertion. Queue-to-window loss propagation, live timer, features, final processing timestamps and capability manifest remain next-phase work. No ML features are claimed frozen.

## Visibility, untested work and decision

| Capability / gate | Result |
| --- | --- |
| Enumeration and genuine OS counters | Demonstrated on selected USB interface |
| S1-01 environment | Partial: capture mapping/version/access unresolved |
| S1-02 independent runtime | Partial: five samples only; no 30-minute idle/controlled run or p95 latency measurement |
| S1-03 real TCP/UDP packet/window gate | BLOCKED: Npcap missing; no real capture attempted |
| S1-04 visibility | Counter boundary recorded; local packet visibility, peer observations, hotspot listing/pre-NAT attribution and monitor mode all NOT TESTED |
| S1-05 resource/failure | Pure caps/reset/gap/error tests passed; working set, CPU, kernel losses, full capture stop timing and sustained load NOT TESTED |
| S1-06 privacy/scope | Foundation retains no payload or capture files; no scans, driver installs, elevation, hotspot/Wi-Fi toggles or network configuration changes |
| S1-07 frozen features | NOT YET TESTED; metadata/window foundation only |
| S1-08 repeatability | Unit/CLI commands run, but fresh controlled packet run and full pass decision remain blocked |

No Django, Next.js, PostgreSQL, Redis, Celery or ML dependency/import/setup exists. No optional sink exists yet; backend-outage resilience has not been tested. No claim about other devices, hotspot clients or monitor mode is supported. Ethernet 3 is the best currently active candidate, not a substitute for a required Wi-Fi gate.

**Exact next action:** operator manually installs Npcap from its official distribution and records version/access options. Then resume the sensor packet phase: re-enumerate without changing network settings, prove the Ethernet 3 OS-to-capture identifier mapping and access, implement the metadata-only Scapy source with bounded queue/loss propagation, and perform a time-bounded authorized controlled TCP/UDP test. If Wi-Fi is the required final observation point, its separate connected-interface test remains mandatory. Do not begin web/ML work.


## Final Sprint 1 decision (current, 2026-09-09)

1. **Final status: PARTIALLY PASSED; NO-GO for Sprint 2.** Current missing
   Ethernet 3 prevents completing the remaining hardware evidence.
2. **Acceptance criteria passed:** S1-01 for the historically recorded profile;
   S1-04 host-first visibility boundary; S1-06 inspected privacy/scope;
   S1-07 seven-feature definitions and hand-calculated fixtures. Prior local
   independent operation, TCP/UDP capture, UDP reference and flow conservation
   remain valid subcriteria, not evidence of a new run.
3. **Acceptance criteria not fully passed:** S1-02 staged sustained operation
   and console latency; S1-03 matched TCP reference and sustained window latency;
   S1-05 sustained resources/real end-to-end shutdown and unavailable HTTP-sink
   integration; S1-08 fresh live repeat and complete go decision.
4. **30-minute stability:** NOT RUN. Reproducible staged validator prepared;
   even its short live smoke attempt was blocked before capture.
5. **Memory/resources:** No live peak/final RSS, CPU or sustained timing result
   for revised code. Telemetry/Windows peak working set and bounded histories
   are implemented; deterministic caps and counted drops pass. Budget <500 MiB.
6. **Packet/flow correctness:** Exact fixtures pass. Historical controlled
   bidirectional TCP/UDP and aggregation conservation remain demonstrated;
   current revised live path cannot be revalidated while adapter is absent.
7. **TCP reference accounting:** NO MATCHED LIVE RESULT. Captured/reference
   counts, bytes and discrepancy are undefined this continuation. Independent
   reference-parser fixture passes; same-interface dual-reader script prepared.
8. **Full test result:** 51/51 unit tests pass; pip check and git diff --check
   pass. Expected Windows line-ending notices are not whitespace failures.
9. **Frozen live contract:** [LIVE_FEATURE_CONTRACT.md](LIVE_FEATURE_CONTRACT.md),
   host-v1, exactly seven reconstructible fields; incomplete windows yield null.
10. **Capability matrix:** Current matrix above uses SUPPORTED, UNSUPPORTED,
    UNTESTED and EXPERIMENTAL only, scoped to actual recorded evidence.
11. **Hardware/network limitations:** Missing USB adapter today; no Wi-Fi/live
    IPv6/remote-device/hotspot/monitor-mode proof. Kernel loss unknown, IP-byte
    accounting subject to shared offload effects; blocked output unproven.
12. **Sufficiently proven for web integration:** **No**, full Sprint 1 gates
    remain open. Reconnect/re-enumerate Ethernet 3 and execute the recorded
    commands; review measurements honestly before revising the decision.
13. **Exact recommended Sprint 2 objective, conditional on full Sprint 1 PASS
    and explicit authorization:** implement one authenticated local live
    vertical slice from the standalone sensor through scoped enrollment and
    idempotent telemetry ingestion into PostgreSQL/Django and a minimal Next.js
    screen. Show real one-second counters and ten-second flows with zero models
    or anomalies; preserve LIVE/source/profile/quality, roles, reconnect/stale
    handling, and initial retention. One ASGI process; no Redis/Celery or ML.
14. **Scope confirmation:** No Django, Next.js, PostgreSQL, Redis, Celery or ML
    was introduced. Dependencies remain psutil 7.2.2 and Scapy 2.7.0; no driver,
    privilege, firewall or network configuration changes were performed.
