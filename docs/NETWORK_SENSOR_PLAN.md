# Windows network sensor plan

## Sprint 1 sign-off - 2026-09-12

**PASS for Ethernet 3 own-host scope.** The corrected scheduler passed the
thirty-minute run with 1,799 valid samples. Fresh live TCP/UDP, numeric host-v1
for complete windows, null partial windows, idle/memory and recovery review pass.
A test-only HTTP mirror demonstrates continued flushed local output after an
actual bounded loopback POST failure, with one attempt and counted discards,
no retries or retained queue. Production sensor code is unchanged by sign-off;
future production HTTP ingestion remains unimplemented. All 93 tests pass.
See the [final gate matrix](SPRINT1_FEASIBILITY_REPORT.md); older partial and
rerun statements below are historical. No later sprint starts automatically.

## Cadence follow-up - 2026-09-12

The official thirty-minute Ethernet 3 run completed normally but emitted only
1,669 valid health records (required at least 1,700). The capture runner now
anchors one-second deadlines to the session monotonic origin so OS collection
and polling overhead do not accumulate. Rates still use actual measurement
intervals; missed deadlines are skipped, never backfilled, and long intervals
remain invalid. New recovery sessions reset the cadence with their baseline.
Recovery bounds, provenance, host-v1 and acceptance thresholds are unchanged.
All 89 offline tests pass; a new live thirty-minute run is required. The latest
[feasibility evidence](SPRINT1_FEASIBILITY_REPORT.md) supersedes older status
and next-step statements below.

## Reduced scope — 2026-09-11

Preserve the existing real Windows Npcap + Scapy sensor, one-second counters/status, ten-second flow windows, frozen host-v1 extraction, bounded same-interface recovery, diagnostic helpers and all tests. No sensor rewrite or dependency change is part of this cleanup. These support Live Network Monitor and Network Recovery & Demo Lab; backend integration is only an optional future sink.

Sprint 1 implementation is almost complete but formal acceptance remains PARTIALLY PASSED / NO-GO. Two USB recoveries were observed; subsequent unexplained process termination and clean thirty-minute stability remain unresolved. The historical "adapter absent"/"Wi-Fi untested" paragraphs below describe their dated evidence and do not establish current connectivity. No live hardware test was run in this scope cleanup.

Broad discovery/inventory, Bluetooth, topology, remote-device traffic claims/models, hotspot/monitor-mode product delivery, browser capture controls, active probes and remote jobs are **OUT OF SCOPE**. Preserve negative/untested capability evidence for S1-04 without scheduling those features. Own-host traffic on one proven observation point remains the baseline; don't infer remote traffic from an endpoint address.

SIMULATION and REPLAY remain explicit module modes. Sprint 5 computes a labelled metadata-only simulation and feature explanations; replay may later use bounded compatible PCAP/controlled inputs. No simulated counters or replay records can become LIVE, and no monitoring gap can become a zero-traffic window.


USB process-termination follow-up: real recovery has now been observed twice,
but one run later ended without normal cleanup evidence. No termination cause
is proven. Opt-in `--process-diagnostics-dir` adds operational lifecycle/PID/time
breadcrumbs and Python fault-handler output; `tests/sensor/stability_observer.py`
records child stdout/stderr and raw OS exit status independently. These are
diagnostics only: capture/recovery ordering, caps, privacy and acceptance rules
are unchanged. See the current feasibility report for evidence and exact rerun.
Fault traces contain stacks without frame locals, not native memory dumps;
forced termination may still produce no in-process traceback.

## Interface-loss recovery (2026-09-09 implementation)

This section supersedes earlier fail-stop-only descriptions for known interface
loss. `capture_status` records use `RUNNING`, `INTERFACE_LOST`, `RECOVERING`,
and `STOPPED`, with LIVE provenance, run/session IDs, UTC observation/loss times,
monotonic run elapsed time, validity and explicit reasons. Loss time means
**detection time**, not the unknowable exact instant the physical link failed.
The one-second interface check bounds normal detection cadence, subject to
scheduling and synchronous OS/output delays.

Known down/missing interfaces, missing OS counters and changed address context
use `InterfaceUnavailable` (a ValueError subclass). Malformed data and unrelated
ValueErrors remain errors and propagate; they are never reclassified by matching
exception text. An unexplained capture-worker failure still fails explicitly.

On detected loss, emit status immediately, mark open windows partial, stop/join
the old worker (two-second join bound), close its socket, drain permitted queued
metadata with partial coverage and flush the old session. No new worker is opened
if shutdown fails. No health samples or synthetic idle windows are produced while
waiting: missing observation cannot establish zero traffic. Status validity is
false during the gap, with no invented byte/packet deltas.

The supervisor waits between attempts. Configurable local API/CLI options are
`recovery_retry_seconds` / `--recovery-retry-seconds` (default 2; 0.1–60 seconds)
and `recovery_timeout_seconds` / `--recovery-timeout-seconds` (default 30; 0–300
seconds; zero disables retries). These are implementation defaults, not measured
hardware-optimal thresholds. Each gap has its own monotonic deadline, bounded
also by the original run deadline; retries do not extend the requested run or
restart its acceptance phase clock. There is no unlimited retry loop. Cancellation
interrupts recovery waits; Ctrl+C remains supported. Synchronous Windows/Scapy
calls and console writes cannot be forcibly interrupted by this deadline: check
the deadline before opening and after readiness, and reject a late restart.
Real end-to-end timing still requires hardware validation.

Each retry rechecks Npcap access and resolves the selected Windows alias/index
to its capture device. Only the original alias and exact GUID-backed Npcap device
identifier may resume; a replacement GUID fails explicitly before socket open.
Addresses are refreshed and the new worker gets a fresh queue, aggregator,
counter baseline and session UUID. A shared run ID relates these separate
sessions. `capture_restarted` carries the new capture context; `RUNNING` with
`reason=interface_recovered` records the completed gap. No network/adapter/driver
configuration changes, elevation or scanning occur. Initial absence terminates
without retry because there is no validated original GUID to recover against.

Timeout emits `STOPPED` / `reason=interface_unavailable` and retains the last
interface diagnostic. The final capture summary aggregates counts and high-water
marks across sessions and records interface-loss count, recovery attempts and
total detected-gap seconds. Epoch health counts remain scoped to their session.
Status consumers must not interpret these records as counter samples.

The stability validator pauses new controlled requests during the gap, refreshes
its IPv4 binding on restart and preserves the original 300/600-second phase
boundaries. An already in-flight request may fail and remains counted. Any
interface loss makes uninterrupted `clean_capture` false, including recovered
runs. Manual/reference validators also reject gapped runs. A diagnostic duration
option is explicitly non-acceptance; the required uninterrupted 1,800 seconds
and every existing numerical threshold remain unchanged.

Current continuation (2026-09-09): [host-v1](LIVE_FEATURE_CONTRACT.md) is frozen
and reconstructed in `sensor/features.py`; health/counter/resource output is
integrated into the local capture runner. Late loss now invalidates subsequent
windows. The new stability/reference scripts are prepared but cannot run live
while Ethernet 3 is absent. The Phase 1B status paragraphs below describe the
earlier implementation; current evidence and limits are in the feasibility report.

Phase 1B implementation status: see [feasibility report](SPRINT1_FEASIBILITY_REPORT.md). Interface enumeration/counters remain independent. The Scapy/Npcap source normalizes outer IPv4/IPv6 headers, queues metadata only and advances ten-second aggregation on a local timer. Windows alias-to-index mapping is checked against Scapy's interface name/index and Npcap identifier. Controlled TCP/UDP capture is proven on Ethernet 3; Wi-Fi and broader attribution remain untested. Features are not implemented/frozen. Noninitial fragments have null ports; all fragments and coarse ICMP/other-protocol groups mark windows partial. ICMP identifiers, reassembly, IPv6 jumbograms and model scoring are unsupported. The initial IPv6 extension walk is bounded to eight headers.

Phase 1B bounds: 20,000 queued records and 10,000 flow entries across open windows; 0 < CLI duration <= 1800 seconds; 50 ms consumer polling; two-second worker join. Scapy uses store=False with one non-promiscuous `ip or ip6` socket and no reassembly/session cache. Flow summaries contain first/last observation and minimum/maximum IP length in addition to aggregate counts. Queue/parser loss conservatively marks all remaining windows in the session partial; kernel loss remains unknown. Large time gaps, clock changes or changed interface/address context stop the session for explicit restart. Output is synchronous console JSON; slow/blocked stdout and sustained load still require the S1-05 benchmark, and a worker join bound alone is not proof of end-to-end five-second shutdown under blocked output.

## Visibility and feasibility gate

The baseline is the laptop's traffic observable on one selected non-loopback interface, subject to Sprint 1 proof. Normal associated Wi-Fi capture is the starting point; monitor mode is not required. Enumerating adapters, access points or neighbour entries does not establish traffic visibility. Other devices' unicast traffic may never reach the capture point. [Wireshark's WLAN guidance](https://wiki.wireshark.org/CaptureSetup/WLAN) describes adapter/platform filtering; [Npcap's guide](https://npcap.com/guide/npcap-users-guide.html) makes raw 802.11 support dependent on hardware/drivers. Do not equate promiscuous mode, monitor mode, AP listing and full-network capture.

| Capability | Initial stance | Sprint 1 evidence required |
| --- | --- | --- |
| Interface enumeration/counters | Expected via psutil and OS metadata | Compare names, addresses and counters with Windows; handle VPN/virtual/disconnected adapters |
| Laptop IP traffic | Primary live scope | Controlled own-host traffic visible with correct adapter, link type, timestamps and counts |
| Other LAN devices | Partial observations only | Record actual ARP/IPv6 neighbour/traffic observations and confidence |
| Hotspot client listing | Experimental | Validate OS API access/permissions on this Windows build; presence is not byte/flow attribution |
| Hotspot client traffic | Experimental | Owned client sends benign known traffic; prove pre-NAT identity on a capturable adapter, both directions and absence of double counting |
| Raw Wi-Fi/monitor mode | Experimental, not MVP | Compatible hardware/driver proof; no assumption of concurrent hotspot/normal Wi-Fi operation |
| Bluetooth presence | OUT OF SCOPE; historical visibility context only | OS permissions/API feasibility; no inference of IP traffic or identity equivalence |

Record Windows build, adapter/driver, Npcap version/options, privilege requirements, capture library versions, and negative results. If hotspot client attribution fails, support laptop-visible traffic only and state this in the UI/report. Npcap installation and privilege elevation are explicit operator setup actions; never silently install drivers or elevate the entire web application.

## Attribution limits and historical hotspot experiment — OUT OF SCOPE delivery

Identify the local host from enrolled sensor identity plus selected-interface addresses. An observed remote IP is a communicating endpoint, not automatically a LAN device or person. A gateway's link-layer address on routed traffic belongs to the next hop, not every remote endpoint. ARP/IPv6 neighbour observations can support local identity, but cache presence does not prove present connectivity or traffic volume. Do not infer client/server role from sorted ports.

The historical Mobile Hotspot experiment design is retained only to explain the evidence required for any future explicitly authorized change; it is OUT OF SCOPE now: enumerate adapters before/after activation, correlate a known client address with controlled traffic, and locate whether observation occurs before or after address translation. Public-side observations may collapse clients behind the laptop; client identity cannot then be reconstructed from public IP/port or timing alone. Even if a client list exists, it does not establish flow visibility. Microsoft's [GetTetheringClients API](https://learn.microsoft.com/en-us/uwp/api/windows.networking.networkoperators.networkoperatortetheringmanager.gettetheringclients) returns client entries and specifies wiFiControl capability; access from this Python/Windows setup remains unverified.

To promote hotspot traffic support, compare traffic from two known clients separately and concurrently where two clients are available; otherwise label evidence single-client only. Record NAT side, link type, address association validity and gaps. Missing client traffic stays unknown, never zero. Do not add driver hooks, forwarding/NAT modification, WFP/ETW integration or router agents merely to rescue this optional feature.

Host/interface-level feature windows are MVP. Remote-device features/models are OUT OF SCOPE. Any future proposal would require sufficient attributable traffic, compatible observation semantics and independent validation. A visible MAC or DHCP/ARP entry alone does not pass this gate. If the selected interface carries unattributable forwarded traffic, label it interface aggregate and do not apply a host-only model.

## Library and process design

Keep the proven Scapy + Npcap implementation. The former PyShark/TShark alternative is historical contingency, not an active dependency or reason to replace working capture. Select one primary adapter. Map psutil interface identifiers to capture identifiers explicitly; similar display names are insufficient.

Planned boundaries: interface adapter/counter sampler, capture source, metadata normalizer, aggregator, observer, pipeline runner, optional transport/spool, local controls and health reporting. Detection remains an imported independent package. Use a bounded queue between capture and processing; callbacks do no persistence or inference. Standalone local operation has no Django imports, database credentials or backend-session prerequisite. Browser command handling is OUT OF SCOPE.

Emit actual one-second interface counter deltas using a monotonic elapsed-time denominator; expose measurement_source=OS_COUNTERS separately from PACKET_METADATA. Counter resets/replacement invalidate one interval rather than yielding negative rates. Counter-only monitoring is LIVE but has capture_capability=OS_COUNTERS_ONLY and no packet feature/model score. psutil counter APIs provide per-interface traffic statistics; they do not provide per-client flows ([psutil API documentation](https://psutil.readthedocs.io/en/latest/#psutil.net_io_counters)).

## Aggregation contract

Normalize packet timestamps to UTC and retain clock/source metadata. Use half-open 10-second event-time windows with 2-second lateness; finalize at window_end + 2 seconds even when no new packets arrive. Use a timer/watermark rather than waiting for the next packet. Within a session/interface, canonically order endpoint tuples, retain directional counters and observed initiator evidence separately. Derive local direction only from validated address context. ICMP uses protocol-specific identifiers/null ports; missing required headers mark incomplete metadata.

Define packet byte metrics as observed IP total length (IPv4) or base-header plus payload length (IPv6) when available; never call this physical-wire or application-payload volume. Count observed IP packets once in a host window, not once per endpoint. OS counter bytes remain a separate series because offload/filter/layer accounting may differ. Npcap notes that [offloading can change observed sizes/checksums](https://npcap.com/guide/npcap-users-guide.html); do not diagnose attacks or require wire-exact totals from these differences.

These are flow segments per time window, not complete transport connections. Long connections span windows; reconnects reusing a tuple within one window coalesce. Do not call segment duration TCP connection duration or infer completed/failed sessions. Late records after finalization increment counters without silently mutating scored windows. Handle truncation, fragments, loopback and non-IP frames explicitly; no payload reassembly. Flush shutdown windows as partial and unscored. Valid zero-traffic host windows can contain zero counts with defined ratios; capture absence/loss yields missing/partial windows, not zero traffic.

Aggregate host window features from the sufficient statistics in ML_METHODOLOGY.md; retain those feature inputs so offline reconstruction matches live inference. Single-interface observation avoids duplicate physical/virtual counts; multi-interface capture is OUT OF SCOPE; earlier experimental notes remain limitations. A network/adapter change, resume from sleep or wall-clock discontinuity closes the old session with a gap and requires a compatible observation profile before scoring. Reset rolling rule context at session changes.

Simulation emits normalized packet metadata in memory, not real network packets, using isolated state and virtual time. PCAP replay later uses the same normalizer/aggregation semantics and preserves original event times; pause/speed controls never alter feature duration. Public feature CSVs that lack requisite metadata cannot be reconstructed into packet streams and remain separate research inputs.

A lab source never labels the laptop's real psutil counters as simulated traffic. Lab charts use the actual generated/replayed metadata summaries at their declared cadence, not invented one-second OS samples. Keep operational runner CPU/heartbeat separate from scenario traffic. Exclude loopback capture from the initial traffic profile; if control-plane traffic later traverses a monitored interface, document any configured exclusion in the packet feature profile while OS interface totals remain unfiltered.

## Bounds and recovery

Provisional caps: 10,000 active flow keys, 20,000 queued metadata records, and metadata-only spool of 50 MiB or 15 minutes, whichever expires first. At the flow-key cap, discard new untracked keys for that window with overflow counters; do not emit multiple conflicting records for the same key/window. Under queue/spool pressure discard oldest records with counted losses. Any known loss affecting a feature window marks it incomplete and suppresses its ordinary ML scoring initially; unknown kernel loss remains a coverage limitation. Bound rolling sets and invalid-batch quarantine within the same storage budget.

Batch to the API using its size/count limits. Separate telemetry from analysis failures and keep stable IDs across retries. Persist only normalized metadata, features and versioned findings in the spool with user-restricted permissions; never packets. Retain the originally used model/rule versions for delayed findings. Old uploads are historical and must not trigger current alerts solely because receipt is recent. Expired session/batch authorization errors quarantine/drop upload explicitly while local capture remains under local operator authority.

Heartbeat proposal: every 5 seconds; mark stale after 15 seconds, configurable after testing. Include capture state, selected adapter, packets observed, parser failures, queue depth, late/dropped records, spool bytes, model version and processing lag. Healthy heartbeat is not proof of complete network visibility. Distinguish idle traffic from stopped capture.

## Local scope and authorization

Interface enumeration and observed flow endpoints are sufficient for the core monitor. Broad passive inventory, active discovery and reachability probes are OUT OF SCOPE. Endpoint presence is not proof of a monitored remote device or its bandwidth. Keep the historical attribution limits above; no discovery subsystem is required.

MVP capture start/stop requires local operator authority and a configured scope. Remote/backend capture commands are OUT OF SCOPE. Future backend authorization protects uploads and reads; it cannot grant OS privileges or revoke offline local capture. A model load failure leaves capture running with ML unavailable. Stop completes within 5 seconds, with partial windows/losses recorded and only a bounded flush attempt. No payload storage by default; discard transient packet buffers immediately. Scapy packet retention and TShark disk capture must be explicitly disabled; a short capture length alone does not guarantee payload privacy. Inspect spool, logs and process/parser outputs during verification.

The exact mandatory feasibility gates and counter-only no-go condition are in [ROADMAP.md](ROADMAP.md). A documented unsupported hotspot result is acceptable; an unverified primary packet path is not.
