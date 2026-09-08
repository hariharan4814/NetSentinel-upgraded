# Product requirements

Status: proposed Sprint 0 baseline, 2026-09-08. Acceptance targets are requirements to verify, not measured results.

## Problem and scope

Provide a demonstrable, explainable view of activity observable from a Windows laptop. Correlate devices, flows, anomalies, health, and incidents without implying complete network surveillance or equating unusual traffic with malicious activity.

Primary users are a student administrator configuring an authorized network, an analyst investigating evidence, and a read-only viewer such as an examiner. The initial deployment is one trusted local workspace with multiple roles, one sensor, and a student laptop. Multi-tenant hosting is out of scope.

## Delivery priorities

| Priority | Capabilities |
| --- | --- |
| MVP / required | One host and one proven capture interface; local sensor controls; one-second real activity/health; bounded flows; local host and observed-peer inventory; minimal reproducible feature schema; offline Isolation Forest training and manual activation/rollback; separate rules and explainable priority; basic incident workflow/in-app alerts; authentication/RBAC; dashboard and short history; seeded Simulation Lab with local launcher; basic CSV report; retention and audit |
| Advanced / after MVP evaluation | Observed communication graph/React Flow; richer analytics and reports; UI-launched lab jobs; browser capture controls; approved reachability probes; PCAP Replay Lab with parser limits |
| Experimental / evidence required | Mobile Hotspot client inventory/traffic attribution; monitor mode; remote-device scoring; public-dataset-to-live feature/model transfer; multi-interface deduplication; broad active discovery |
| Optional / no submission dependency | Bluetooth context, AI explanation assistant, external threat intelligence, supervised-model comparison, Redis deployment expansion; Celery on a separately justified supported runtime |

Hotspot visibility and broader discovery depend on feasibility evidence. A failed hotspot experiment must reduce the documented scope rather than trigger fake live data. Incident response initially means acknowledgment, triage, notes, evidence review, resolution, and suggested actions. Automated enforcement is excluded. Neither packet count nor discovery proves complete device traffic visibility. In host-only scope, the dashboard answers which observable host/endpoint needs attention; it must not imply visibility of every connected device.

## Functional acceptance

| ID | Requirement and observable acceptance |
| --- | --- |
| FR-01 | Server enforces administrator, analyst, viewer, and scoped sensor permissions; unauthorized REST and socket access fails. |
| FR-02 | Enumerate available interfaces and distinguish available, selected, active, unsupported, and failed capture states. Record actual visibility and missing privileges. |
| FR-03 | Start/stop an authorized capture session locally without Django; show one-second samples, heartbeat, drops, lag, and stale state. Browser control is advanced. Counter-only fallback shows no fabricated flows or ML scores. |
| FR-04 | Store local host identity and actually observed peers, address evidence, first/last seen and confidence. Remote IPs are endpoints, not automatically discovered LAN devices. Full device attribution is experimental. |
| FR-05 | Produce timestamped bounded flow windows and versioned behavioural features without persisted packet payloads. |
| FR-06 | Train, evaluate, approve, activate, and roll back versioned models; incomplete or incompatible models cannot silently score live records. |
| FR-07 | Show anomaly score, threshold, model version, feature context, separate rule evidence, and uncertainty. No ML-derived attack label. |
| FR-08 | Correlate important findings into incidents with distinct classification, severity, lifecycle, evidence, and audit history. Deduplicate repeat alerts. |
| FR-09 | Dashboard answers network health, current activity, anomalies/incidents, and devices needing attention. WebSocket reconnect recovers authoritative state. |
| FR-10 | MVP provides short history, sensor/interface health, a bounded CSV report and audit logs. Rich history and topology are advanced. Health describes measured collection/link state, not an asserted secure or healthy entire network. |
| FR-11 | Simulation scenarios use the shared aggregation/rule/incident path with permanent SIMULATION badges; a fixed rule fixture reliably demonstrates investigation even if ML returns no anomalies. Replay is advanced and preserves original and processing time. |
| FR-12 | Settings cover capture scope, retention, alert policy, and active model; sensitive changes require authorization and audit. |

## Quality targets

Reference benchmark: provisionally Windows laptop with 4 CPU cores and 8 GB RAM; record actual hardware before accepting performance results. Sprint 1 requires a 30-minute own-host run including idle and controlled traffic, with sensor memory below 500 MiB and bounded queues. A later 1,000-packet/s, 50-synthetic-subject stress workload is a capacity experiment, not a promise to observe 50 real devices. The 10,000 active flow-key cap is a safety limit, not expected sustained capacity. Target total application memory below 3 GiB; profile and document revisions before expanding scope.

Two cadences: actual interface samples every second, with p95 sample-end-to-dashboard latency below 3 seconds after integration; behavioural windows every 10 seconds, finalized after at most 2 seconds of lateness, with p95 finalization-to-dashboard latency below 3 seconds. Thus a packet near a window's start may wait about 15 seconds for a finding, longer under declared degradation. Heartbeats are every 5 seconds; stale after 15 seconds. No interpolation can invent intervening values. Target p95 common filtered API reads below 500 ms with 100,000 flow records. The pipeline must stay bounded under overload and expose losses. No accuracy target is asserted before evaluation.

Use DATABASE_PLAN.md's age, row and byte budgets from the first persistence sprint; retention is not postponed to final polish. Zero detections is a valid result: live rates, totals, recent flows, observed peers, coverage, model status and history remain useful.

Other release gates: keyboard-accessible primary workflows, readable projector presentation, no secrets in version control, no default payload storage, mode isolation, repeatable migration/restore procedure, and deterministic evaluation artifacts.

## Explicit exclusions and assumptions

No credential interception, decryption of third-party communications, unauthorized scanning, internet-wide monitoring, malware execution, automatic blocking, or claim of complete attack prevention. Laptop visibility is constrained by interface, network topology, privileges, and driver support. Optional AI is not an authoritative classifier. Demonstrations use owned or explicitly authorized devices and benign synthetic scenarios.
