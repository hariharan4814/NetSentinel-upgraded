# Architecture review and scope decision

## Reduced final-project review — 2026-09-11

**Accepted scope:** NetSentinel: An Intelligent Real-Time Network Monitoring and Anomaly Detection System. Preserve all existing Sprint 1 code, dependencies, tests and evidence. Sprint 0 is complete; Sprint 1 implementation is almost complete, but its formal result remains **PARTIALLY PASSED / NO-GO for Sprint 2**. This review changes documentation only and authorizes no web/database/ML setup.

The four final modules are **Live Network Monitor**, **Anomaly Detection Engine**, **Explainable Threat Analysis**, and **Network Recovery & Demo Lab**. Their scientific claims are limited to actual observations and compatible features: unusual does not imply malicious, Normal does not imply safe, and unscored/missing data does not become Normal or zero.

| Prior planning item | Current decision |
| --- | --- |
| Administrator/analyst/viewer product, JWT/ticket orchestration | Advanced RBAC OUT OF SCOPE; use minimal local operator authentication and scoped ingestion with server-side checks. |
| Incidents, risk/asset weights, case transitions/notes, alerts and notifications | OUT OF SCOPE; retain computed feature/rule explanations and evidence, without a response workflow. |
| Broad devices/inventory, discovery, topology/React Flow and remote-device models/claims | OUT OF SCOPE; selected-interface metadata and flow endpoints only. Preserve historical visibility limitations/negative evidence. |
| Bluetooth, threat intelligence APIs, AI chatbot/LLM explanations | OUT OF SCOPE; explanations are local and based on observed statistics. |
| Celery, automatic remote jobs/capture controls, microservices/cloud requirements | OUT OF SCOPE; local CLI operations and modular Django. Redis only after a documented essential need; REST polling first. |
| Multi-model comparisons and enterprise report/export systems | OUT OF SCOPE; one Isolation Forest with valid evaluation, recent charts and academic report support. |
| A1/A2/X expansion and former Sprint 7 | Removed from active roadmap. Seven sprints 0–6; final integration/submission is Sprint 6. Compatible replay is staged within the lab and can follow later. |
| Risk-55/one-incident simulation fixture | Superseded by two computed window rule findings and zero benign-control findings; ML can be disabled. No hardcoded results. |
| Seven frozen host-v1 features and S1-01–S1-08 | Unchanged. Port/flow counts for explanations come from retained metadata, not silent model-vector expansion. |

Revised roadmap: 0 planning (complete); 1 real sensor/stability/recovery (almost complete, acceptance partial); 2 Django REST/PostgreSQL; 3 Next.js monitor; 4 genuine baseline/Isolation Forest; 5 feature explanations and labelled Simulation/Replay; 6 integration, evaluation, polish, documentation and viva.

Reasons/consequences/status are recorded in ARCHITECTURE.md ADR-019/020. Product/API/database/module/design/testing plans now describe only necessary core support. SECURITY_RULES.md is also aligned because its former mandatory roles/JWT/socket design contradicted the reduced API plan; basic access control, CSRF, credential separation and privacy remain mandatory.

Remaining evidence: unexplained USB process termination after two observed recoveries; no accepted uninterrupted 1,800-second run; matched live TCP reference, sustained resource/latency/full stop measurements, fresh live repeat and unavailable-HTTP-sink integration remain open. The latter is not proved by an injected preflight exception. Current adapter availability is unknown in this cleanup; older absent-adapter claims are historical.

Validation: the full existing sensor suite passed **86/86 in 2.657 seconds**, exit 0. SHA-256 comparison confirms existing non-document files, including sensor/tests/dependencies, are unchanged from the starting working tree. All eight gate rows and the frozen live contract are unchanged; historical evidence is preserved. All 46 local Markdown links resolve. `git diff --check` passed, exit 0, with LF/CRLF notices only. No new hardware/capture, model accuracy or backend capability is claimed.

## Historical Sprint 0 review — preserved evidence, superseded scope

The complete 2026-09-08 review below is retained as history. Its enterprise/advanced/experimental delivery tiers, incident/risk fixture, six-app proposal and Sprint 7/A1/A2/X recommendations are **OUT OF SCOPE or superseded** by the decision above. Statements about absent implementation/tests/hardware describe that review date only. Its scientific, privacy, independent-sensor and Sprint 1 feasibility reasoning remains useful; historical recommendations are not active authorization.

# Historical Sprint 0 architecture and feasibility review

Review date: 2026-09-08. Scope: all 14 original Sprint 0 files together. Result: documentation corrected; implementation remains conditional on the standalone Windows feasibility gate. No hardware capture, model evaluation, dependency installation or application tests were performed in this review.

## A. Critical findings

1. **Attribution was ahead of evidence.** The original ML plan derived device windows first while the sensor plan admitted missing attribution. A peer/IP/MAC observation is not evidence of complete per-device traffic. Corrected to host/selected-interface MVP; Mobile Hotspot pre-NAT attribution and remote-device models remain experimental.
2. **Visible real time lacked a fast data source.** Ten-second windows plus lateness do not yield one-second dashboard activity. Added actual one-second interface samples, separate from finalized flow/detection updates, with distinct freshness and byte semantics.
3. **Independent operation was underspecified.** Capture was outside Django, but session/control/model references implied backend dependencies. Added local session IDs, local authorization and output, optional HTTP transport, pending/applied model versions, and telemetry that survives invalid/missing analysis.
4. **Feature reproducibility was incomplete.** Inter-arrival, short-flow and flag features were proposed without the necessary stored state. Time-window flow segments are not complete connections. Reduced the MVP to seven reconstructible host features and deferred features requiring extra state.
5. **Dataset transfer was too permissive.** Public flow CSVs cannot become equivalent live packet windows simply by mapping feature names. Added a measurement-semantic compatibility gate and separate offline experiments for incompatible data.
6. **Demonstration reliability depended on uncertain findings.** A seed fixes inputs, not the behaviour of every trained model. Added a fixed rule/policy fixture that produces a computed incident with ML disabled; scientific test data stays separate.
7. **Storage and runtime boundaries needed stronger limits.** Ten thousand active keys can produce 86.4 million window rows/day. Seven-day retention and late cleanup were not credible at that load. Added early age/row/byte budgets and operational cleanup. Channels needed explicit same-ASGI-process ingestion; Celery's native-Windows suitability was not addressed.

The scientific distinction between anomaly and attack was already correct and has been preserved. PostgreSQL and a modular monolith are suitable choices; neither needs replacement with microservices or a specialized database before measurement.

## Review of the 24 requested checks

| # | Check | Conclusion and correction |
| --- | --- | --- |
| 1 | Cross-document contradictions | Corrected device-first versus uncertain attribution, API/CLI job execution, model activation versus actual load, feature inputs, retention timing and demonstration guarantees across all plans |
| 2 | Windows Wi-Fi visibility | Normal host-associated capture is the target. Promiscuous/monitor mode cannot promise all clients; hardware validation remains required |
| 3 | Mobile Hotspot | Client listing, packet visibility and per-client attribution are separate experimental results. No implication that a virtual adapter necessarily exposes usable traffic |
| 4 | Anomaly versus attack | Preserved explicit separation; no-alert/no-score is not a secure-network verdict |
| 5 | Isolation Forest categories | Correctly an unusualness model; labels arise from distinct evidence, never the forest alone |
| 6 | Public/live features | Added compatibility manifest, exact extraction parity, observation/label-unit checks and live domain-shift evaluation |
| 7 | Per-device attribution | Local host identity is feasible to test; remote endpoints stay observations until supported. NAT/gateway MAC cannot establish client traffic |
| 8 | Capture/aggregation/ML/Django | Capture callback, processing queue, reusable detection and web persistence have separate responsibilities; no capture/training in requests |
| 9 | Independent sensor | Required without Django/database/model; local controls/output and bounded optional upload |
| 10 | PostgreSQL | Suitable for bounded aggregates; stage tables/indexes, retain evidence snapshots, test cleanup and storage headroom early |
| 11 | Redis/Celery | Neither required for MVP; Celery excluded from native-Windows runtime, future deployment needs a separate decision |
| 12 | Channels before Redis | Local-demo only: one ASGI process handles HTTP ingestion and sockets; sensor/CLI publish through HTTP, REST reconciles losses |
| 13 | Privacy | Payload restriction now includes library retention/temp files/debug/spool; metadata, identifiers and research exports still require minimization |
| 14 | ML-triggered actions | No blocking/scanning/driver changes; anomaly alone cannot open an incident under the initial policy. Investigation requires rule evidence; sensitive operations stay authorized |
| 15 | Scope | Original long feature sequence reduced to seven implementation sprints, including evaluation, with advanced work after MVP |
| 16 | Priority tiers | Explicit MVP, advanced, experimental and optional tiers in product/roadmap/module plans |
| 17 | Failures | Added sleep/resume, counter reset, clock/profile change, counter-only fallback, old uploads, analysis mismatch, runner absence and storage pressure |
| 18 | Provenance | Immutable modes, run-isolated lab identity/state/credentials, model eligibility, DB/API/socket/report tests; physical interface not invented for lab sources |
| 19 | Academic evaluation | Chronological grouped splits, development/demo separation, explicit label unit, no undefined metrics, reviewed false-alert denominator and session-level variation |
| 20 | Deterministic demo | Computed rule-driven fan-out incident plus benign control, ML disabled, same pipeline, no preloaded incident rows |
| 21 | Live UI | Real one-second samples, separate packet/OS units, source timestamps, no timer-generated chart values, active zero-anomaly workflows |
| 22 | Windows-first validation | Exact Sprint 1 gates precede Django/Next.js development and any advanced work |
| 23 | Unproven hardware | Hotspot, monitor mode, client visibility, alternate adapters and Bluetooth labelled experimental; unsupported is a legitimate recorded result |
| 24 | Technical debt | Six staged Django apps, minimal features, local controls before job runners, applied-model acknowledgment, record-level dedup, explicit byte/profile semantics and early retention reduce avoidable rework |

## B. Important changes made

Updated AGENTS.md, README.md and all 11 original docs to use the same constrained MVP and gates. Reviewed .gitignore and left it unchanged: its exclusions cover sensitive artifacts/runtime data and retain future dependency lockfiles. Added this review as an evidence trail; authoritative operational definitions remain in their linked plans.

- [Architecture](ARCHITECTURE.md): independent sensor, two data cadences, isolated telemetry/analysis upload, local Channels restriction, polling recovery, revised decisions.
- [Sensor plan](NETWORK_SENSOR_PLAN.md) and [ML methodology](ML_METHODOLOGY.md): honest attribution, reconstructible host features, compatible datasets, deterministic integration demonstration.
- [Database](DATABASE_PLAN.md), [API](API_PLAN.md) and [security](SECURITY_RULES.md): staged persistence, bounds, version/provenance validation, revocation limits and local authorization.
- [Product](PRODUCT_REQUIREMENTS.md), [modules](MODULES.md), [design](DESIGN_SYSTEM.md), [testing](TESTING_STRATEGY.md) and [roadmap](ROADMAP.md): reduced scope, visible no-anomaly usefulness, common acceptance gates.

## C. Deferred and experimental features

Advanced: topology/React Flow, rich analytics/reports, browser capture controls, UI-launched job runners, approved reachability probes and PCAP Replay Lab. Experimental until proven: Mobile Hotspot listing/attribution, monitor mode, remote-device scoring, multi-interface deduplication, broad active discovery and public-dataset model transfer. Optional: Bluetooth, AI explanation, threat intelligence and supervised comparisons. Redis is a deployment option, not an MVP feature; Celery would require a supported runtime decision.

## D. Remaining technical risks

| Risk | Next evidence / owner boundary |
| --- | --- |
| Actual laptop interface capture or Npcap access fails | Sprint 1 sensor evidence; counter-only mode does not pass the packet gate |
| Hotspot client traffic is absent or post-NAT only | Experimental sensor result; retain host/interface scope rather than escalating implementation complexity |
| Packet offload, partial headers, interface identity or clock behaviour changes observations | Sensor fixtures/reference comparison and profile compatibility validation |
| Live benign baseline is sparse/contaminated or drifts | ML collection manifest, independent sessions and transparent exploratory limitations |
| Rule/risk thresholds cause alert fatigue | Calibration, benign controls and weight/threshold sensitivity analysis; formula is a proposed heuristic |
| Student-laptop PostgreSQL write/cleanup/resource budget is insufficient | Staged end-to-end load and disk-growth measurements; reduce retained detail/scope |
| Single-process Channels drops events/restarts | REST snapshots and polling; any deployment expansion requires a shared layer decision |
| Model artifacts require elevated trust; offline capture cannot be remotely revoked | Local operator procedures, credential revocation and verified artifact origin; no false security guarantee |
| Submission time cannot cover advanced modules | Deliver Sprint 7 before A1/A2/X; reconcile schedule with the actual academic deadline |

## E. Exact recommended Sprint 1 objective

Prove that an independently runnable, metadata-only Python sensor can produce visible, genuinely live interface counters and correct bounded packet/flow summaries from at least one intended non-loopback interface on the actual Windows student laptop, without Django, Next.js, PostgreSQL, Redis, Celery or an ML model. Establish the visibility boundary and freeze a small live-compatible feature contract before web development.

## F. Mandatory Sprint 1 completion evidence

[ROADMAP.md](ROADMAP.md) defines the authoritative S1-01 through S1-08 gates: recorded environment; independent one-second output/30-minute run; two-direction TCP and UDP packet/window correctness; visibility matrix; resource/failure bounds; privacy/authorization; fixed feature contract; and fresh-process repeatability with pass/no-go conclusion. All must pass. Host support can pass while hotspot/monitor mode remain unsupported or untested. Counters-only, simulation-only and loopback-only are not substitutes for the intended-interface packet gate.

## G. Scope confirmation and primary evidence

This review creates/edits documentation only. No production application code, framework project, environment, dependency manifest or installed package was created. Documentation checks cannot prove real hardware capability; Sprint 1 experiments remain future work.

Windows visibility restrictions are supported by [Wireshark WLAN capture guidance](https://wiki.wireshark.org/CaptureSetup/WLAN) and [Npcap's user guide](https://npcap.com/guide/npcap-users-guide.html). Hotspot client enumeration has a documented [Microsoft API and capability requirement](https://learn.microsoft.com/en-us/uwp/api/windows.networking.networkoperators.networkoperatortetheringmanager.gettetheringclients), which is not proof of per-client packet visibility in this environment. The host-first fallback is an engineering conclusion from these limits, not a vendor guarantee.

[Channels](https://channels.readthedocs.io/en/latest/topics/channel_layers.html) documents the in-memory process limitation; [Celery](https://docs.celeryq.dev/en/main/faq.html#windows) documents lack of Windows support. [IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) and [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) support the score semantics and split discipline. [CICIDS2017's publisher](https://www.unb.ca/cic/datasets/ids-2017.html) describes flow features/captures; NetSentinel requires its own compatibility validation, and claims no dataset has passed that gate.
