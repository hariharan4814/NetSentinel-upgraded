# Sequential roadmap

Reduced scope accepted 2026-09-11: seven sprints numbered **0–6**. Sprint 0 is
complete; **Sprint 1 PASS for Ethernet 3 own-host scope, 2026-09-12**. Later
implementation requires explicit authorization and the preceding gates; this
sign-off does not start Django, Next.js, PostgreSQL or ML work.

| Sprint | Deliverables | Exit gate and dependencies |
| --- | --- | --- |
| 0 — Planning and architecture | Project requirements, boundaries, scientific/privacy principles and acceptance plan | Complete; later scope decisions update this baseline without rebuilding the sensor. |
| 1 — Real Windows sensor | Existing Npcap/Scapy capture, one-second telemetry, ten-second flows/features, stability, gaps and safe recovery | PASS on Ethernet 3; all S1-01 through S1-08 evidenced in the final feasibility report. No shortened/gapped diagnostic counts as uninterrupted acceptance. |
| 2 — Django REST + PostgreSQL | Simple backend, telemetry/flow/interface/status APIs, bounded persistence, local source registration and minimal authentication | Requires full S1 PASS and explicit setup authorization. Genuine sensor records persist/read back with provenance, idempotency, authorization, migrations, gaps and retention; optional sink failure cannot stop local monitoring. No dashboard/ML prerequisite. |
| 3 — Next.js dashboard | Current upload/download, packets, TCP/UDP, active flow summaries, interface/sensor status and traffic charts | Real accepted data updates with no model or anomalies; source/units/mode visible, stale/gap/reconnect/cache separation tested, display latency measured. Start with bounded REST polling. |
| 4 — Isolation Forest anomaly detection | Confirm frozen host-v1, collect reviewed genuine baseline, train/calibrate one model, trusted save/load, score live ten-second windows | Feature/preprocessing parity, session-separated splits, locked threshold/test evaluation, actual model versions, Normal / Anomalous and score; incompatible/partial/no-model data stays unscored and telemetry continues. |
| 5 — Explainable analysis + Simulation/Replay | Feature-based explanations, controlled anomaly scenarios, isolated modes, deterministic rule-driven viva demo; compatible replay source when supported | Explanations cite actual deviations/statistics and limitations; benign control and repeated SIMULATION compute expected rule findings with ML disabled. LIVE/SIMULATION/REPLAY separation tested. PCAP/controlled-data replay requires compatibility/privacy/parser gates; if not delivered, show unavailable and document limitation. |
| 6 — Final integration and completion | End-to-end tests, UI polish, measured performance/stability, final research evaluation, documentation, screenshots, report support and viva rehearsal | Useful genuine live monitor, honest Normal / Anomalous evaluation, labelled safe demo, explicit gaps/visibility limits, local startup/restore and final evidence. No enterprise/cloud requirement. |

## Removed roadmap tracks — OUT OF SCOPE

The former Sprint 2 roles/JWT/frontend bundle, Sprint 3 inventory/lab bundle, Sprint 5 incident workflow, Sprint 6 reporting/admin scope, Sprint 7 submission slot and A1/A2/X expansion tracks are superseded. Final evaluation/submission is now Sprint 6. Compatible replay is staged in module 4/Sprint 5 and may be completed later; it is not an enterprise expansion track.

Do not schedule advanced RBAC, complex incidents/risk/alerts, Bluetooth, topology, intelligence APIs, AI/LLM, Celery, enterprise notifications, remote-device traffic claims/models, multi-model research, enterprise reporting, broad inventory, unjustified microservices, required cloud deployment, browser capture/job controls or active discovery. Redis requires a separately documented essential need. Historical decisions and hardware experiments remain evidence only.

## Exact Sprint 1 objective

Prove that an independently runnable, metadata-only Python sensor can produce visible, genuinely live interface counters and correct bounded packet/flow summaries from at least one intended non-loopback interface on the actual Windows student laptop, without Django, Next.js, PostgreSQL, Redis, Celery or an ML model. Establish the visibility boundary and freeze a small live-compatible feature contract before web development.

## Mandatory Sprint 1 success criteria

Sign-off, 2026-09-12: **Sprint 1 PASS for the selected Ethernet 3 host profile**.
Accepted uninterrupted thirty-minute run, exact matched TCP reference, fresh
TCP/UDP/windows/features, idle/memory review and real unavailable-HTTP-sink
independence are recorded in the latest feasibility report. All 93 tests pass.
Historical termination cause remains unproven; recovery evidence and current
clean completion are separately documented. All eight gate rows and numerical
tolerances below are unchanged. Sprint 2 requires explicit authorization.

All eight criteria require recorded evidence; a proposal or source citation is not hardware validation. Store evidence in [SPRINT1_FEASIBILITY_REPORT.md](SPRINT1_FEASIBILITY_REPORT.md) with sanitized observations and commands/configuration, never private captures. Phases 1A/1B are authorized and recorded there. Phase 1B demonstrates real bidirectional TCP/UDP and flow aggregation on Ethernet 3; it does not complete all eight gates. The remaining sprints are not authorized by this implementation.

| Gate | Required evidence to pass |
| --- | --- |
| S1-01 — Environment | Record actual Windows build, CPU/RAM, Python/capture library, Npcap and adapter/driver versions, installation/privilege needs and selected OS-to-capture interface mapping. Choose Scapy if sufficient; test PyShark only if correctness/performance gaps justify its TShark dependency. |
| S1-02 — Independent visible operation | With Django and PostgreSQL absent/stopped and no model, locally start/stop the sensor and display actual selected-interface samples every second. Record a 30-minute run including at least 5 minutes idle and 5 minutes controlled own-host activity; p95 sample-end-to-console delay at most 2 seconds. No dashboard is required in this sprint. |
| S1-03 — Packet and window correctness | On the intended non-loopback interface, identify both directions of at least one controlled TCP exchange and a controlled UDP exchange; produce addresses/ports/protocol, observed lengths/counts and 10-second windows finalized within the 2-second lateness allowance plus at most 1 second local processing (p95). If Wi-Fi is intended, Wi-Fi must pass; Ethernet cannot silently substitute. Use same-interface/filter/time-bound reference metadata or generated fixtures: fixture counts exact, controlled capture counts within 5% of the matched reference. Explain offload/filter differences; unmatched results do not pass until reconciled. |
| S1-04 — Visibility and attribution | Publish supported/unsupported/not-tested results for local traffic, peer observations, hotspot client listing, hotspot pre-NAT packet attribution and monitor mode. Mark untested capabilities experimental. Host-first scope passes without hotspot/monitor mode. Claim a hotspot client only after known client traffic is mapped to its pre-NAT identity; otherwise use unknown/aggregate attribution. |
| S1-05 — Failure and resource bounds | During the run record sensor working-set memory below 500 MiB, CPU, queue/flow counts, losses and output latency; inject queue pressure with metadata fixtures and demonstrate configured caps and counted drops. Demonstrate idle versus stopped capture, unavailable adapter/permission error (safe fault injection allowed), restart, sleep/resume or equivalent clock-gap handling, and unavailable HTTP sink while local output continues. Stop and flush/mark partial state within 5 seconds. |
| S1-06 — Privacy and scope | Inspect produced files/logs: only permitted metadata, no payload dump, tokens or private model artifacts. Confirm one explicitly selected interface, local operator authorization, no automatic scanning/blocking, and no driver installation/elevation hidden in startup. |
| S1-07 — Frozen minimum contract | Document byte units, direction, flow key, observed/finalized/processed timestamps, empty/partial-window policy, capability flags and the live host feature v1 definitions from ML_METHODOLOGY.md. Hand-calculated fixtures cover zero traffic, two directions, boundaries and missing headers. Record features unsupported by the actual capture point. No ML training or public-dataset model is needed. |
| S1-08 — Repeatability and decision | Repeat local start/stop and controlled-traffic observation in a fresh process using recorded steps. Document a pass/no-go conclusion and remaining experimental capabilities; update affected plans. Counters-only, loopback-only or simulation-only results are useful fallback evidence but do not pass the intended-interface packet gate. If that gate fails, stop advanced work and obtain an explicit scope/hardware decision. |

## Demonstration and contingency

Show selected LIVE interface/source/capabilities, generate benign authorized own-laptop traffic and show real rates/protocols/flows even with zero anomalies. Where a compatible model is available, show Normal / Anomalous, score/threshold and evaluated-window coverage. Explicitly select SIMULATION, run the local deterministic scenario and explain computed feature/rule evidence. No incident acknowledgment/resolution/export workflow is required.

The ML_METHODOLOGY.md demonstration uses a benign control and generated fan-out metadata with a fixed transparent rule. Findings are computed, never inserted as expected dashboard rows; ML can be disabled. A scenario pass is integration evidence, not attack-detection accuracy. REPLAY must select a supported input/profile and preserve original event time; unavailable replay stays visibly unavailable.

If capture fails during the viva, disclose the failure and monitoring gap. Retain genuine OS counters only if available, and switch explicitly to a labelled lab. Recovery or simulation cannot retroactively pass Sprint 1. Keep gaps, private metadata handling, source limitations and honest research results in the final report.
