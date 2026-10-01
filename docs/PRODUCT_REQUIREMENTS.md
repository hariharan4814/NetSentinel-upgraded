# Product requirements

## Current public product — 2026-10-01

User-authorized pivot: serve everyday people with slow or unreliable internet.
The implemented public MVP provides a bounded HTTP response check, symptom-led
troubleshooting, optional local history/comparison/deletion, report download,
manual-speed download planner and a how-to/privacy guide. Acceptance and limits
are in ../plan.md and PUBLIC_RELEASE.md. It works without a sensor/backend/model.
No whole-network health, speed-test or security claim is made.

The original monitor remains a local advanced tool at `/local`. All requirements
below apply to that historical research pipeline unless superseded by ADR-028.
The public build contains none of the private monitoring routes or data.

**NetSentinel: An Intelligent Real-Time Network Monitoring and Anomaly Detection System**

Reduced final-project scope accepted 2026-09-11. Sprint 0 planning is complete.
**Sprint 1 PASS for Ethernet 3 own-host scope, 2026-09-12**; see the exact
[acceptance evidence](SPRINT1_FEASIBILITY_REPORT.md). Requirements and proposed
targets for later sprints below are not measured results. No later implementation
is authorized by this sign-off.

## Problem and scope

Provide a defensible M.Sc. final-year demonstration of genuine network activity observable from one selected interface on a Windows student laptop, unusual traffic windows, and explanations supported by observed metadata. The primary operator is the student; an examiner can observe the local demonstration. No enterprise organization or role hierarchy is required.

## Four core modules

| Module | Required capability and acceptance |
| --- | --- |
| Live Network Monitor | Npcap + Scapy capture; real upload/download rates, packet counts, TCP/UDP/protocol information, active flow summaries and interface/sensor status. One-second telemetry and ten-second analysis windows. Runs locally without Django, PostgreSQL, a model or backend network access. |
| Anomaly Detection Engine | One Isolation Forest trained on genuine traffic-derived features for the matching host/interface profile; trusted local save/load; score complete ten-second windows as Normal or Anomalous with score, threshold and actual model version. Unavailable/incomplete is neither Normal nor Anomalous. |
| Explainable Threat Analysis | Human-readable deviations from an appropriate baseline and transparent rule evidence: high packet rate, traffic spike, unusually high outbound traffic, many destination ports or unusual flow count when supported by retained statistics. These are descriptive observations, not proven causes or attacks. |
| Network Recovery & Demo Lab | Detect selected-interface loss, record gaps and recover safely within existing bounds. Preserve LIVE / SIMULATION / REPLAY mode and source/run identity. Provide a deterministic, rule-driven, labelled simulation; replay support is staged and may later use bounded PCAP or compatible controlled data. |

Active flows mean observed flow keys in a stated window, not confirmed established TCP connections. Remote endpoints are not an inventory of monitored devices. Existing host-v1 has seven frozen model inputs; additional explanation statistics must be computed from retained metadata and versioned separately, without silently changing the model vector.

## Functional acceptance

| ID | Requirement and observable acceptance |
| --- | --- |
| FR-01 | Use minimal local authentication as needed; enforce server-side access to telemetry and sensitive actions. A separate scoped ingestion credential cannot access operator routes. Advanced RBAC is OUT OF SCOPE. |
| FR-02 | Enumerate and distinguish available, selected, active, unavailable and failed interface/capture states, with actual visibility and privilege limitations. |
| FR-03 | Locally start/stop authorized capture independently; publish real one-second samples and bounded ten-second flow windows. Counter-only fallback has no fabricated packet protocols, flows or ML scores. |
| FR-04 | Preserve directional packet/IP-byte counts, protocol, endpoints, timestamps, sufficient statistics, quality and version information. Default storage is metadata and aggregates only. |
| FR-05 | Persist a bounded short history through a simple Django REST backend and PostgreSQL. Expose live telemetry, flow summaries, interface status, sensor status and monitoring gaps. |
| FR-06 | Freeze/confirm features, collect reviewed genuine baseline sessions, train/calibrate/evaluate one Isolation Forest, save/load a trusted versioned artifact and score compatible complete windows. No public model becomes LIVE merely because column names match. |
| FR-07 | Display Normal / Anomalous, anomaly score, calibrated threshold, model version and coverage. Anomaly does not equal attack; no score is an attack probability or secure-network verdict. |
| FR-08 | Explain observed deviations with feature value, unit, baseline/reference, rule threshold/version where used, limitations and plausible benign alternatives. Unsupported evidence is unavailable. Malware, attack, exfiltration or port-scan wording may only be tentative and supported by actual evidence; omit unsupported labels. |
| FR-09 | Keep dashboard useful with zero anomalies or no model: upload/download, packets, TCP/UDP, recent active flows, traffic charts and live sensor/interface status. Label measurement source, observed time and partial/stale state. |
| FR-10 | On interface loss, expose invalid coverage and bounded recovery of the same verified interface identity; reset session, counters and aggregation. Monitoring gaps are not zero traffic. Recovery does not pass uninterrupted stability. |
| FR-11 | Run a deterministic SIMULATION from generated metadata through aggregation and transparent rules; compute explanations with ML disabled, never preinsert findings. REPLAY retains original and processing times and uses explicit compatibility checks; unsupported replay inputs stay unavailable. |
| FR-12 | Demonstrate mode isolation, local capture authorization, bounded resources, failure handling, metadata privacy and reproducible evaluation. No automatic blocking or network reconfiguration. |

## Quality targets and unchanged Sprint 1 gates

[ROADMAP.md](ROADMAP.md) S1-01 through S1-08 remain mandatory and unchanged. The actual Windows laptop is the reference; record its hardware/profile. Require an uninterrupted 30-minute own-host run including at least five minutes idle and five minutes controlled activity, working-set memory below 500 MiB, measured CPU/queues/losses and timing, matched TCP/UDP evidence and fresh-process repeatability. Queue and active-flow caps remain safety limits, not claimed sustainable database throughput.

After integration, proposed p95 sample-end-to-dashboard latency is below three seconds for one-second telemetry; p95 finalized-window-to-dashboard latency is below three seconds for ten-second windows after the two-second lateness allowance. A packet near a window's start can therefore wait roughly fifteen seconds for analysis. Freshness uses observation time. Proposed heartbeat cadence is five seconds, stale after fifteen; this external consumer is not implemented yet. Never invent intervening chart values.

Retain the proposed total application memory target below 3 GiB and p95 common filtered API reads below 500 ms at 100,000 flow records, subject to measured review. Apply DATABASE_PLAN.md age/row/byte limits from Sprint 2. No accuracy target is asserted before evaluation. Keyboard accessibility, projector readability, explicit errors and a reproducible local startup/demo procedure are final acceptance requirements.

## OUT OF SCOPE

Removed from the active roadmap, rather than promised as later sprints: advanced RBAC and user-management workflows; complex incident management (assignment, acknowledgment, triage, notes, resolution and case timelines); weighted enterprise risk/asset scoring; Bluetooth monitoring; network topology/React Flow; threat intelligence APIs; AI chatbot/LLM explanations; Celery; Redis unless a later measured necessity is explicitly approved; enterprise notification workflows; remote-device traffic monitoring claims/models; complex multi-model ML comparisons; large enterprise reporting and export-job systems; broad device inventory/discovery; microservices unless a core architectural need is demonstrated; and cloud deployment as a project requirement.

Browser capture controls, remote job runners, active reachability/scanning features, rich analytics and dedicated reporting screens are also removed from active delivery. Simple recent traffic charts, diagnostic evidence and academic report support remain. Prior enterprise plans and experimental visibility observations in ARCHITECTURE_REVIEW.md and SPRINT1_FEASIBILITY_REPORT.md are historical evidence, not authorization.

## Scientific and privacy principles

Anomaly does not equal attack. LIVE traffic must be genuine; SIMULATION and REPLAY must stay labelled in every record/view and cannot contaminate a live baseline. Missing observation is unknown, not zero. Document interface, NAT, driver/offload, protocol and attribution limits; never imply full-network or remote-device visibility. Prefer metadata and aggregates, do not persist payloads by default, and keep private metadata, captures, credentials and model artifacts out of Git. Demonstrations use owned/authorized scope and benign controlled activity; no unauthorized scanning, malware execution, credential interception or automatic enforcement.
