# Product requirements

Status: proposed Sprint 0 baseline, 2026-09-08. Acceptance targets are requirements to verify, not measured results.

## Problem and scope

Provide a demonstrable, explainable view of activity observable from a Windows laptop. Correlate devices, flows, anomalies, health, and incidents without implying complete network surveillance or equating unusual traffic with malicious activity.

Primary users are a student administrator configuring an authorized network, an analyst investigating evidence, and a read-only viewer such as an examiner. The initial deployment is one trusted local workspace with multiple roles, one sensor, and a student laptop. Multi-tenant hosting is out of scope.

## Delivery priorities

| Priority | Capabilities |
| --- | --- |
| Core demonstration | Authentication/RBAC; interface selection; real sensor health and metadata; device inventory; flow analytics; feature extraction; baseline/model lifecycle; anomalies; rule interpretation; risk; incidents and in-app alerts; uncluttered live dashboard; labelled Simulation Lab; audit events |
| Completion after core | Historical analytics, observed topology, network health, report exports, settings and retention management |
| Later | PCAP/dataset Replay Lab; optional Bluetooth presence; optional AI incident explanations; external threat intelligence; supervised classification experiments |

Hotspot visibility and broader discovery depend on feasibility evidence. A failed hotspot experiment must reduce the documented scope rather than trigger fake live data. Incident response initially means acknowledgment, triage, notes, evidence review, resolution, and suggested actions. Automated enforcement is excluded.

## Functional acceptance

| ID | Requirement and observable acceptance |
| --- | --- |
| FR-01 | Server enforces administrator, analyst, viewer, and scoped sensor permissions; unauthorized REST and socket access fails. |
| FR-02 | Enumerate available interfaces and distinguish available, selected, active, unsupported, and failed capture states. Record actual visibility and missing privileges. |
| FR-03 | Start/stop an authorized capture session outside the web process; show heartbeat, drops, lag, and stale state. Stopping traffic must not leave a fabricated active chart. |
| FR-04 | Store observable device identities, address changes, first/last seen, and connection history with source and confidence. Unknown identities remain unknown. |
| FR-05 | Produce timestamped bounded flow windows and versioned behavioural features without persisted packet payloads. |
| FR-06 | Train, evaluate, approve, activate, and roll back versioned models; incomplete or incompatible models cannot silently score live records. |
| FR-07 | Show anomaly score, threshold, model version, feature context, separate rule evidence, and uncertainty. No ML-derived attack label. |
| FR-08 | Correlate important findings into incidents with distinct classification, severity, lifecycle, evidence, and audit history. Deduplicate repeat alerts. |
| FR-09 | Dashboard answers network health, current activity, anomalies/incidents, and devices needing attention. WebSocket reconnect recovers authoritative state. |
| FR-10 | Provide time-filtered history, observed topology, health indicators, reports, and audit logs; disclose collection gaps and partial visibility. |
| FR-11 | Simulation scenarios run deterministically through shared aggregation/detection with permanent SIMULATION badges. Replay later preserves original and processing time. |
| FR-12 | Settings cover capture scope, retention, alert policy, and active model; sensitive changes require authorization and audit. |

## Quality targets

Reference benchmark: provisionally Windows laptop with 4 CPU cores and 8 GB RAM; record actual hardware before accepting performance results. Initial budget: 30-minute run with approximately 1,000 observed packets/s, 50 device identities, 10,000 active flow keys, sensor+detection memory below 500 MB, and total application memory below 3 GB. Measure CPU, loss, and throughput; revise targets transparently after feasibility testing.

Use 10-second event-time windows initially. Target p95 closed-window-to-dashboard latency below 3 seconds on the reference machine; this does not mean subsecond packet detection. Target p95 common filtered API reads below 500 ms with 100,000 flow records. The pipeline must stay bounded under overload and expose losses. No accuracy target is asserted before evaluation.

Other release gates: keyboard-accessible primary workflows, readable projector presentation, no secrets in version control, no default payload storage, mode isolation, repeatable migration/restore procedure, and deterministic evaluation artifacts.

## Explicit exclusions and assumptions

No credential interception, decryption of third-party communications, unauthorized scanning, internet-wide monitoring, malware execution, automatic blocking, or claim of complete attack prevention. Laptop visibility is constrained by interface, network topology, privileges, and driver support. Optional AI is not an authoritative classifier. Demonstrations use owned or explicitly authorized devices and benign synthetic scenarios.
