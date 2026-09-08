# Sprint 1 feasibility evidence

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
