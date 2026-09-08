# Sequential roadmap

Sprint lengths are planning estimates of 1–2 weeks after Sprint 0. Proceed by acceptance evidence, not calendar alone. Scope reductions must be recorded. Implementation requires a subsequent user instruction.

| Sprint | Deliverables | Exit gate and dependencies |
| --- | --- | --- |
| 0 — Foundation | This documentation, agent rules, ignore policy | All requested documents agree; no application code or scaffolds |
| 1 — Windows feasibility | Authorized minimal sensor experiment; enumerate adapters; compare Scapy/PyShark; measure local capture, hotspot visibility, privileges, overhead | Record hardware/OS/driver versions, observable protocols, packet counts versus reference capture, failures and capability matrix. Choose capture adapter and baseline laptop budget; hotspot can be explicitly unsupported |
| 2 — Application skeleton and access | Authorized Next.js/Django setup; PostgreSQL migrations; roles/JWT; settings validation; single-process ASGI configuration | Login/logout and role tests pass; protected REST/socket handshake works; documented Windows startup; no real capture in web process |
| 3 — Live telemetry vertical slice | Sensor enrollment, sessions, heartbeats, bounded capture/aggregation, ingestion contract, flow persistence, basic live screen | Real authorized traffic reaches UI; idempotent retries, stale state, overload and no-payload tests pass; measure latency |
| 4 — Devices and health | Passive discovery, address history, interface health, limited opt-in probes, flow filters | Known test devices observed where visible; unknown identity and collection gaps remain explicit; no full-network claim |
| 5 — Features and research baseline | Versioned feature extraction; reviewed normal sessions; chronological split; offline training/evaluation registry | No leakage; reproducible seed/config; rule-only baseline; locked evaluation plan and trusted artifact manifest |
| 6 — Anomalies and interpretation | Sensor inference, model activation/rollback, rules, risk policy, cold-start behaviour | Anomaly versus suspicion separated; score direction tested; explanations and model/rule versions stored; failures preserve collection |
| 7 — Incident response and alerts | Correlation, deduplication, workflow, notes, audit and in-app notifications | Repeat windows do not flood alerts; invalid transitions/roles rejected; closure is audited; no automatic blocking |
| 8 — Simulation and demo reliability | Deterministic normal/burst/fan-out/device-churn scenarios, shared pipeline, visible mode switch | Repeated seeds reproduce inputs; actual pipeline findings shown even if no anomaly is produced; no live/synthetic contamination; complete core demo |
| 9 — Dashboard and historical completion | Refined accessible dashboard, historical charts, observed topology, reports, retention and settings | Four dashboard questions answered; provenance/gaps in exports; keyboard and projector review; indexed queries and restore validated |
| 10 — Replay Lab | Bounded PCAP import/parser isolation, event-time replay, reproducible dataset mapping | Same metadata yields equivalent features within documented parser tolerance; no payload persistence by default; replay cannot trigger live actions |
| 11 — Evaluation and final submission | Locked test evaluation, performance and security checks, dissertation results/limitations, demo script | Report measured false alerts, precision/recall only where ground truth exists, latency/resources, reproducibility and unsupported visibility |
| 12 — Optional extensions | Bluetooth, evidence-linked AI explanations, threat intelligence or supervised comparison | Only after core gates; separate authorization/privacy review and measured benefit; no dependency for final demonstration |

## Demonstration and contingency

Core sequence: sign in → show LIVE source/interface/health → generate benign traffic on an owned device → show actual flows → inspect a finding if one exists → explicitly switch to SIMULATION → run a seeded scenario → inspect actual model/rule output and incident evidence → acknowledge/resolve → export a mode-labelled report.

Live anomaly creation is not guaranteed. If capture fails, show the real failure and use the visibly separate Simulation Lab. Keep sanitized prepared replay material for the later replay milestone. Never promise that a fixed scenario must trigger a particular learned model: select and document evaluated demo configurations without fabricating results.

If time contracts, defer Sprint 10 and Sprint 12; preserve real telemetry, scientific evaluation, simulation separation, incident workflow, and Sprint 11 validation. Reduce chart/report breadth before weakening provenance or security. Track sensor visibility, model quality, and performance as continuing risks with evidence owners in their respective plans.
