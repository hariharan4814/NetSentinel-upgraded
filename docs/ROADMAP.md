# Sequential roadmap

## Active next roadmap — AI Lab, 2026-10-04

Follow A1–A8 in the active [plan.md](../plan.md): contracts and protocol →
independent simulator → genuine training and group-separated evaluation →
explanations → bounded local jobs → experiment UI → reports/viva → integration
and measurement. The optional grounded assistant, external benchmark and public
recorded showcase follow the core. Implementation is underway; the current plan records which of those
new implementation milestones have been verified. Keep the previous product/source;
defer its unresolved production Windows release work for the new AI core.
Historical stages/evidence below are not evidence that the AI Lab is complete.

## 2026-10 Windows Companion and Public Product Upgrade

The user explicitly authorized implementation and release preparation for a broader MSc project delivery comprising:
1. **Public Web Helper**: Static client-side connection check, measured Cloudflare speed test, visitor-side IP/provider lookup, guided troubleshooting, download planner, and privacy-first client-side PDF export.
2. **Windows Companion Developer Preview (v0.2.0)**: Authenticated loopback dashboard (port 8765), per-executable traffic attribution, daily/monthly quotas, opt-in firewall enforcement, Windows Defender status queries and explicit scan controls, and private PDF reports.
3. **Local Research Stack Hardening**: Scoped bearer token authentication in Django and HttpOnly session cookies with CSRF validation at Next.js `/local`.

### Phase Status & Acceptance Gates (Tracked in `plan.md` & `YT.md`):
- **P0 Planning & Baseline**: VERIFIED. Dedicated branch `codex/windows-companion-release`.
- **P1 Attribution & Sockets**: VERIFIED. Canonical SHA-256 IDs, process socket matching, wildcard address-family conservatism, unmatched traffic labeled unassigned.
- **P2 Quotas & SQLite v1**: VERIFIED. Daily/monthly thresholds, warn percent, persistent intent, restart survival.
- **P3 Narrow Broker & Firewall**: VERIFIED (mock/PowerShell fixture) / Privileged live execution BLOCKED. NetSecurity block/unblock, lease recovery, origin rejection, critical binary protection.
- **P4/P5 Windows Defender & Firewall Status**: IMPLEMENTED & VERIFIED read-only. Real Defender Normal/active, 3 firewall profiles queried.
- **P6 Bounded Flow Events**: IMPLEMENTED. Outbound burst, new destination, unusual port metadata.
- **P7 Measured Speed Testing**: VERIFIED. Cloudflare speed test integration, nominal 15.5 MB budget, unit math and cancellation tested.
- **P8 Visitor IP Lookup**: VERIFIED. Client-side ipwho.is query, consent-gated, default redacted.
- **P9 Semantic PDF Reports**: VERIFIED. Client-side jsPDF + local companion ReportLab with privacy defaults.
- **P10 Integrated UI & Auth**: VERIFIED. Glassmorphism vanilla CSS, 52/52 frontend unit tests, 29/29 E2E browser tests, ESLint clean, Next.js build clean.
- **P11 Windows Packaging**: IMPLEMENTED. Source installer ZIP (`NetSentinel-Companion-0.2.0.zip`), SHA-256 digest manifest, hash-locked wheels, third-party notices. Hardened Program Files broker installation deferred.
- **P12 Public Release Artifact**: VERIFIED. Generated static allowlist in `public-release/dist`. Deployment to remote Sites service requires active user session credentials.

**Historical evidence:** sprint reports below describe earlier checks. Outstanding release gates and current AI Lab acceptance are tracked in plan.md; do not treat these historical totals as a new complete acceptance run.

- **Sprint 0:** Planning & Architecture — COMPLETE.
- **Sprint 1:** Native Windows Sensor & Safe Recovery (`Ethernet 3`) — PASS (committed at `ea8819a`).
- **Sprint 2:** Django REST & PostgreSQL Foundation — PASS (committed at `7fb7281`).
- **Sprint 3:** Next.js Monitoring Dashboard — PASS (committed at `79ee41b`).
- **Sprint 4:** Isolation Forest ML Pipeline (335 LIVE windows, threshold 0.7191) — PASS (committed at `a7cfdb5`).
- **Sprint 5:** Feature Explainability & Light Theme UI Redesign — PASS (committed at `793ae85`).
- **Sprint 6:** Final Integration, Demonstration Readiness & Viva Guide — COMPLETE & VERIFIED.

| Sprint | Deliverables | Exit gate and dependencies | Status |
| --- | --- | --- | --- |
| 0 — Planning and architecture | Project requirements, boundaries, scientific/privacy principles and acceptance plan | Complete; later scope decisions update this baseline without rebuilding the sensor. | COMPLETE |
| 1 — Real Windows sensor | Existing Npcap/Scapy capture, one-second telemetry, ten-second flows/features, stability, gaps and safe recovery | PASS on Ethernet 3; all S1-01 through S1-08 evidenced in the final feasibility report. | COMPLETE |
| 2 — Django REST + PostgreSQL | Simple backend, telemetry/flow/interface/status APIs, bounded persistence, local source registration and minimal authentication | Genuine sensor records persist/read back with provenance, idempotency, authorization, migrations, gaps and retention. | COMPLETE |
| 3 — Next.js dashboard | Current upload/download, packets, TCP/UDP, active flow summaries, interface/sensor status and traffic charts | Real accepted data updates with no model or anomalies; source/units/mode visible, stale/gap/reconnect/cache separation tested. | COMPLETE |
| 4 — Isolation Forest anomaly detection | Confirm frozen host-v1, collect reviewed genuine baseline, train/calibrate one model, trusted save/load, score live ten-second windows | 335 genuine LIVE windows (180 train / 60 cal / 60 test), calibrated threshold ~0.7191, strict score bounds. | COMPLETE |
| 5 — Explainable analysis + Simulation/Replay | Feature-based explanations, controlled anomaly scenarios, isolated modes, deterministic rule-driven viva demo; light theme UI redesign | Lightweight percentile-based explainability, neutral vocabulary, no attack claims, dynamic serializer support, Roboto font. | COMPLETE |
| 6 — Final integration and completion | End-to-end tests, UI polish, measured performance/stability, final research evaluation, documentation, screenshots, report support and viva rehearsal | Full real pipeline verification (Session 4), 209 automated tests passing, comprehensive viva guide, complete master documentation. | COMPLETE |

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
