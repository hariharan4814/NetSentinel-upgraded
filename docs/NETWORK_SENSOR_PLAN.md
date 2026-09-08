# Windows network sensor plan

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
| Bluetooth presence | Later, separate context | OS permissions/API feasibility; no inference of IP traffic or identity equivalence |

Record Windows build, adapter/driver, Npcap version/options, privilege requirements, capture library versions, and negative results. If hotspot client attribution fails, support laptop-visible traffic only and state this in the UI/report. Npcap installation and privilege elevation are explicit operator setup actions; never silently install drivers or elevate the entire web application.

## Attribution and hotspot boundaries

Identify the local host from enrolled sensor identity plus selected-interface addresses. An observed remote IP is a communicating endpoint, not automatically a LAN device or person. A gateway's link-layer address on routed traffic belongs to the next hop, not every remote endpoint. ARP/IPv6 neighbour observations can support local identity, but cache presence does not prove present connectivity or traffic volume. Do not infer client/server role from sorted ports.

Mobile Hotspot is a separate experiment: enumerate adapters before/after activation, correlate a known client address with controlled traffic, and locate whether observation occurs before or after address translation. Public-side observations may collapse clients behind the laptop; client identity cannot then be reconstructed from public IP/port or timing alone. Even if a client list exists, it does not establish flow visibility. Microsoft's [GetTetheringClients API](https://learn.microsoft.com/en-us/uwp/api/windows.networking.networkoperators.networkoperatortetheringmanager.gettetheringclients) returns client entries and specifies wiFiControl capability; access from this Python/Windows setup remains unverified.

To promote hotspot traffic support, compare traffic from two known clients separately and concurrently where two clients are available; otherwise label evidence single-client only. Record NAT side, link type, address association validity and gaps. Missing client traffic stays unknown, never zero. Do not add driver hooks, forwarding/NAT modification, WFP/ETW integration or router agents merely to rescue this optional feature.

Host/interface-level feature windows are MVP. Remote-device features/models require sufficient attributable traffic, compatible observation semantics and independent validation. A visible MAC or DHCP/ARP entry alone does not pass this gate. If the selected interface carries unattributable forwarded traffic, label it interface aggregate and do not apply a host-only model.

## Library and process design

Try Scapy first for direct Python metadata handling. Evaluate PyShark/TShark only if the spike reveals a correctness/overhead problem that it may solve; record the decision rather than requiring two installations by default. PyShark adds a TShark executable dependency. Select one primary adapter. Map psutil interface identifiers to capture identifiers explicitly; similar display names are insufficient.

Planned boundaries: interface adapter/counter sampler, capture source, metadata normalizer, aggregator, observer, pipeline runner, optional transport/spool, local controls and health reporting. Detection remains an imported independent package. Use a bounded queue between capture and processing; callbacks do no persistence or inference. Standalone local operation has no Django imports, database credentials or backend-session prerequisite. Browser command handling is advanced.

Emit actual one-second interface counter deltas using a monotonic elapsed-time denominator; expose measurement_source=OS_COUNTERS separately from PACKET_METADATA. Counter resets/replacement invalidate one interval rather than yielding negative rates. Counter-only monitoring is LIVE but has capture_capability=OS_COUNTERS_ONLY and no packet feature/model score. psutil counter APIs provide per-interface traffic statistics; they do not provide per-client flows ([psutil API documentation](https://psutil.readthedocs.io/en/latest/#psutil.net_io_counters)).

## Aggregation contract

Normalize packet timestamps to UTC and retain clock/source metadata. Use half-open 10-second event-time windows with 2-second lateness; finalize at window_end + 2 seconds even when no new packets arrive. Use a timer/watermark rather than waiting for the next packet. Within a session/interface, canonically order endpoint tuples, retain directional counters and observed initiator evidence separately. Derive local direction only from validated address context. ICMP uses protocol-specific identifiers/null ports; missing required headers mark incomplete metadata.

Define packet byte metrics as observed IP total length (IPv4) or base-header plus payload length (IPv6) when available; never call this physical-wire or application-payload volume. Count observed IP packets once in a host window, not once per endpoint. OS counter bytes remain a separate series because offload/filter/layer accounting may differ. Npcap notes that [offloading can change observed sizes/checksums](https://npcap.com/guide/npcap-users-guide.html); do not diagnose attacks or require wire-exact totals from these differences.

These are flow segments per time window, not complete transport connections. Long connections span windows; reconnects reusing a tuple within one window coalesce. Do not call segment duration TCP connection duration or infer completed/failed sessions. Late records after finalization increment counters without silently mutating scored windows. Handle truncation, fragments, loopback and non-IP frames explicitly; no payload reassembly. Flush shutdown windows as partial and unscored. Valid zero-traffic host windows can contain zero counts with defined ratios; capture absence/loss yields missing/partial windows, not zero traffic.

Aggregate host window features from the sufficient statistics in ML_METHODOLOGY.md; retain those feature inputs so offline reconstruction matches live inference. Single-interface observation avoids duplicate physical/virtual counts; multi-interface capture is experimental. A network/adapter change, resume from sleep or wall-clock discontinuity closes the old session with a gap and requires a compatible observation profile before scoring. Reset rolling rule context at session changes.

Simulation emits normalized packet metadata in memory, not real network packets, using isolated state and virtual time. PCAP replay later uses the same normalizer/aggregation semantics and preserves original event times; pause/speed controls never alter feature duration. Public feature CSVs that lack requisite metadata cannot be reconstructed into packet streams and remain separate research inputs.

A lab source never labels the laptop's real psutil counters as simulated traffic. Lab charts use the actual generated/replayed metadata summaries at their declared cadence, not invented one-second OS samples. Keep operational runner CPU/heartbeat separate from scenario traffic. Exclude loopback capture from the initial traffic profile; if control-plane traffic later traverses a monitored interface, document any configured exclusion in the packet feature profile while OS interface totals remain unfiltered.

## Bounds and recovery

Provisional caps: 10,000 active flow keys, 20,000 queued metadata records, and metadata-only spool of 50 MiB or 15 minutes, whichever expires first. At the flow-key cap, discard new untracked keys for that window with overflow counters; do not emit multiple conflicting records for the same key/window. Under queue/spool pressure discard oldest records with counted losses. Any known loss affecting a feature window marks it incomplete and suppresses its ordinary ML scoring initially; unknown kernel loss remains a coverage limitation. Bound rolling sets and invalid-batch quarantine within the same storage budget.

Batch to the API using its size/count limits. Separate telemetry from analysis failures and keep stable IDs across retries. Persist only normalized metadata, features and versioned findings in the spool with user-restricted permissions; never packets. Retain the originally used model/rule versions for delayed findings. Old uploads are historical and must not trigger current alerts solely because receipt is recent. Expired session/batch authorization errors quarantine/drop upload explicitly while local capture remains under local operator authority.

Heartbeat proposal: every 5 seconds; mark stale after 15 seconds, configurable after testing. Include capture state, selected adapter, packets observed, parser failures, queue depth, late/dropped records, spool bytes, model version and processing lag. Healthy heartbeat is not proof of complete network visibility. Distinguish idle traffic from stopped capture.

## Discovery and authorization

MVP discovery is passive observations and available neighbour/interface metadata. Active discovery is experimental and approved reachability probes are advanced: opt-in, scoped to owned/authorized targets, rate-limited, logged and cancellable. Probe failure is not proof a device is down. Use “not recently seen” rather than “disconnected” when evidence is absent.

MVP capture start/stop requires local operator authority and a configured scope. Advanced backend commands additionally require administrator authorization and local acceptance; they cannot grant OS privileges. A model load failure leaves capture running with ML unavailable. Stop completes within 5 seconds, with partial windows/losses recorded and only a bounded flush attempt. No payload storage by default; discard transient packet buffers immediately. Scapy packet retention and TShark disk capture must be explicitly disabled; a short capture length alone does not guarantee payload privacy. Inspect spool, logs and process/parser outputs during verification.

The exact mandatory feasibility gates and counter-only no-go condition are in [ROADMAP.md](ROADMAP.md). A documented unsupported hotspot result is acceptable; an unverified primary packet path is not.
