# Frozen minimum live feature contract

Status: **host-v1, frozen for Sprint 1**, 2026-09-09. Exactly seven ordered values;
no model, training or public-dataset feature is introduced. Implementation:
`sensor/features.py`; hand-calculated tests: `tests/sensor/test_completion.py`.
This contract freezes calculation semantics; it does not certify sustained capture.

## Shared measurement semantics

One locally authorized host, one selected non-loopback interface, immutable LIVE
session UUID, `measurement_source=PACKET_METADATA`. Current demonstrated hardware
profile is Ethernet 3 / Samsung USB / Windows ifIndex 23 with Scapy 2.7.0 and
Npcap 1.88, non-promiscuous BPF `ip or ip6`. This adapter must be present and its
mapping revalidated at each start. Counter samples are a separate OS_COUNTERS series.
Never substitute OS bytes for packet IP bytes.

All seven values are **derived** from observed outer-IP metadata. IPv4 bytes are
the IP total-length field; IPv6 bytes are 40 plus payload length. Include IP and
transport headers, retransmissions and duplicate observations. Exclude link-layer
overhead; do not claim physical-wire or application-byte accounting. No reassembly,
deduplication, clipping, imputation, normalization or log transform occurs.

Direction uses the selected interface's canonical local address set: source only
local is outbound; destination only local is inbound; both/neither is unknown.
Remote peer means the opposite IP endpoint, never a discovered LAN device/person.
Each window record retains `local_addresses` for reconstruction; protect this
metadata as a private inventory. An address/interface change terminates the session.
Bounded recovery may start a **new** session on the revalidated original alias/GUID
with refreshed addresses. A run ID groups sessions without merging their windows.

Flow key: `(interface, protocol, sorted(source IP/port, destination IP/port))`
inside a session and window. Sorting is textual canonical IP then port, null before
numeric ports. Protocol separates TCP/UDP; null headers never imply zero ports.
These are ten-second flow segments, not whole transport connections.

Every feature uses the same epoch-aligned UTC half-open window `[start,start+10)`.
Denominator for rates is **10 seconds**, never first-to-last packet duration.
Packet `timestamp` is the capture event's UTC Unix seconds; `first_observed` and
`last_observed` are min/max packet timestamps per segment. Window start/end are
integer Unix seconds. `finalized_at` is the event-watermark UTC time when closed
at end+2 seconds (or partial shutdown watermark); `processed_at` is wall-clock UTC
Unix seconds at serialization. They are separate from any future receipt time.
Window timing applies identically to all seven fields below.

## Exact ordered fields

Let N = attributable IP packets, B = their IP bytes, O/I = outbound/inbound IP
bytes, T = TCP packets, S = TCP packets with SYN set including SYN+ACK, U = UDP
packets and R = set of remote IPs across attributable flows in this window.

| Order / name | JSON type | Unit / formula | Direction | Missing / unavailable | Validation |
| --- | --- | --- | --- | --- | --- |
| 1 packets_per_second | number (float64 calculation) | packets/s = N/10 | inbound + outbound once each | Whole vector null under policy below | Exact counts and two window boundary fixture |
| 2 ip_bytes_per_second | number (float64) | IP bytes/s = B/10 | both | Whole vector null | Hand sums and live DNS IP-length reference |
| 3 outbound_byte_fraction | number (float64) | dimensionless O/(O+I) | outbound numerator | Whole vector null; idle 0 | 100 outbound / 200 total = 0.5 |
| 4 unique_remote_peers | integer | distinct canonical IP count = len(R) | remote endpoint in either direction | Whole vector null; idle 0 | Deduplicate same peer across ports/protocols; second peer adds one |
| 5 tcp_syn_fraction | number (float64) | dimensionless S/T | TCP in both directions; includes SYN+ACK | Whole vector null; no TCP 0 | Two TCP packets both SYN set gives 1 |
| 6 udp_fraction | number (float64) | dimensionless U/N | UDP in both directions | Whole vector null; idle 0 | One UDP / three IP = 1/3 |
| 7 mean_ip_packet_bytes | number (float64) | IP bytes/packet = B/N | both | Whole vector null; idle 0 | 200/3 bytes |

## Completeness, bounds and versioning

`feature_schema_version=host-v1`; flow JSON remains additive `phase1b-flow-v1`.
`features` is the named object in the table's order or JSON null. Partial or
unfinalized windows, missing local context, unknown direction, missing required
TCP/UDP headers, parser errors, fragmentation, coarse ICMP/OTHER handling, queue
loss, overflow and shutdown suppress the entire vector. Do not silently calculate
a subset from a partial window or replace missing fields with zeros. Unsupported
ICMP semantics and IPv6 jumbograms are outside this profile. IPv6 parser fixtures
pass; intended-interface live IPv6 correctness remains untested.

Capture known active with a complete empty window yields seven zeros. Stopped
capture produces no subsequent idle windows. Startup/shutdown fragments are
partial. Late packets are counted and rejected; finalized windows are immutable;
remaining session windows are conservatively partial after late/queue/parser loss.
No retroactive completeness correction is made to an already emitted window.
Counter gaps >3 seconds invalidate rates; capture watermark gaps >30 seconds or
wall/monotonic mismatch >1 second terminate capture and require a new session.
No 15-second external heartbeat/stale consumer or HTTP sink is implemented yet.

Known interface loss closes the old session with all open/queued windows partial
and feature vectors null. During recovery there are status events but no counter
samples or generated empty windows: absent observation is unknown, not measured
idle. A restarted session uses a fresh counter baseline and aggregator; its
startup fragment is partial. Windows must never bridge or combine sessions across
the gap, even if their epoch-aligned start times coincide. Later fully observed
windows may again be complete. Already emitted windows are not rewritten; loss
detection time is recorded, and the physical start of loss remains uncertain.
These are completeness/provenance clarifications; host-v1's seven calculations,
byte units, 10-second denominator and null policy are unchanged.

`partial=false` means no known application loss, **not** complete physical capture.
`kernel_loss=unknown` is always retained. Required capability context consists of
LIVE mode, packet measurement source, selected mapping, filter, promiscuous=false,
local-address context, schema version and partial/kernel-loss flags. No remote
device or full-network capability is implied. Backend integration must preserve
this context; later profile/version changes cannot silently reuse this contract.

At most 20,000 queued metadata records, 10,000 flow entries across at most two
open windows; peer reconstruction uses a temporary set bounded by those entries.
No persistent feature history or model exists. Preserve flow endpoint tuples,
directional packet/byte counts, total packets/bytes, protocol, SYN counts and
quality flags to reconstruct each value exactly. Numeric fixture tolerance is
1e-12 absolute for fractions; integer counts are exact.

## Hand-calculated fixtures (no transmitted traffic)

Documentation host 192.0.2.1 and peer 198.51.100.2, SIMULATION test provenance:

| Time (UTC epoch seconds) | Metadata | IP bytes |
| --- | --- | --- |
| 1 | host:1234 -> peer:443 TCP SYN | 60 |
| 2 | peer:443 -> host:1234 TCP SYN+ACK | 100 |
| 9 | host:1234 -> peer:443 UDP | 40 |

Window [0,10), finalized at 12: N=3, B=200, O=100, I=100, T=2, S=2, U=1,
R={198.51.100.2}. Vector = **[0.3,20,0.5,1,1,1/3,200/3]**.
Only UDP differs in transport; this is metadata, not an asserted valid application
exchange. Two protocol flows still contain one remote IP.

Boundary fixture: a 60-byte outbound SYN at 9.999 and another at exactly 10
belong respectively to [0,10) and [10,20). Each vector is
**[0.1,6,1,1,1,0,60]**, finalized at 12 and 22.
Empty active [0,10) -> **[0,0,0,0,0,0,0]**. A packet with null required source
port -> partial window and **null**, not a zero vector. A shutdown window is null.
These fixture results prove calculations only; live hardware evidence is separate
in [SPRINT1_FEASIBILITY_REPORT.md](SPRINT1_FEASIBILITY_REPORT.md).
