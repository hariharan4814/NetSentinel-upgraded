# NetSentinel

**NetSentinel: An Intelligent Real-Time Network Monitoring and Anomaly Detection System**

An M.Sc. final-year project for genuine network monitoring on a Windows laptop, Isolation Forest anomaly detection, observed-feature explanations and a safe, clearly labelled demonstration lab.

**Status:** Sprint 0 complete. **Sprint 1 PASS on Ethernet 3, 2026-09-12.** Real Npcap/Scapy TCP/UDP capture, aggregation, seven-feature generation, recovery and process diagnostics are demonstrated within the recorded host-profile limits; **93/93 tests pass**. No backend, dashboard or trained model is implemented. Sprint 2 requires a separate explicit implementation request.

The corrected scheduler passed the uninterrupted thirty-minute run with 1,799 valid samples, all checks true and exit 0. Matched TCP reference discrepancy is 0%; fresh-process TCP/UDP, windows/features, idle/memory review and actual HTTP-outage independence pass. Recovery cleanup evidence is sufficient for this scope; the historical abrupt exit's cause remains unproven. [Final acceptance matrix and evidence](docs/SPRINT1_FEASIBILITY_REPORT.md) supersede older partial-status statements.

## Four core modules

| Module | Scope |
| --- | --- |
| Live Network Monitor | Npcap + Scapy; real upload/download, packets, TCP/UDP/protocol information, active flow summaries, interface/sensor status; one-second telemetry and ten-second analysis windows. |
| Anomaly Detection Engine | One Isolation Forest trained on genuine traffic-derived features; compatible complete windows labelled Normal / Anomalous with score and threshold. |
| Explainable Threat Analysis | Observed feature deviations and transparent rules explain unusual rates, outbound volume, destination ports and flow counts where supported. No unsupported attack labels or LLM. |
| Network Recovery & Demo Lab | Detect interface loss, preserve monitoring gaps and safely recover within existing bounds. Explicit LIVE / SIMULATION / REPLAY modes; deterministic simulation, with compatible replay support staged later. |

An anomaly is not an attack and its score is not attack probability. Missing or unscored data is not Normal; monitoring gaps are not zero traffic. LIVE is genuine, simulation/replay stay labelled, and synthetic data never silently enters a live baseline. Capture is limited to the selected observation point; remote endpoints do not establish other-device or full-network visibility. Prefer metadata/aggregates and never persist payloads by default.

The standalone sensor works without Django, PostgreSQL, a model or backend connectivity. The future HTTP sink is optional; the browser only presents accepted data. Monitoring stays useful with zero anomalies.

## Seven-sprint roadmap

| Sprint | Goal / status |
| --- | --- |
| 0 | Planning and architecture — complete. |
| 1 | Real Windows sensor, capture, flows, telemetry, stability and recovery — PASS for Ethernet 3 own-host scope. |
| 2 | Simple Django REST + PostgreSQL foundation, telemetry/flow/interface APIs, bounded persistence and minimal authentication. |
| 3 | Next.js dashboard: rates, packets, TCP/UDP, flows, interface/sensor state and traffic charts. |
| 4 | Confirm frozen features, genuine baseline, Isolation Forest train/save/load/score and documented evaluation/threshold. |
| 5 | Feature-based explanations, controlled scenarios, labelled Simulation/Replay and safe viva demo. PCAP/controlled-data replay is staged by compatibility. |
| 6 | End-to-end tests, UI polish, performance/stability, final documentation/screenshots/report support and viva preparation. |

All original [Sprint 1 acceptance gates](docs/ROADMAP.md) are satisfied without changing their thresholds. No later sprint is started by this sign-off.

## Planned stack and exclusions

Keep the existing Python 3.11 sensor with pinned Scapy/psutil and manually installed Npcap. Future stack: Django REST Framework + PostgreSQL, Next.js/TypeScript with simple charts, and scikit-learn Isolation Forest with trusted local artifact handling. Select web/ML dependency versions only during authorized setup. Start with REST polling; add push only for demonstrated need.

**OUT OF SCOPE:** advanced RBAC; complex incident management and weighted enterprise risk scoring; Bluetooth; topology/React Flow; threat intelligence APIs; chatbot/LLM explanations; Celery; Redis unless later essential; enterprise notifications; remote-device traffic monitoring claims/models; complex multi-model comparisons; large reporting systems; broad inventory/discovery; unjustified microservices; required cloud deployment. Remote capture/job controls and enterprise export workflows are also removed. Historical evidence remains labelled in the review and feasibility report.

## Planning documents

- [Agent instructions](AGENTS.md)
- [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Four module responsibilities](docs/MODULES.md)
- [Roadmap and unchanged acceptance gates](docs/ROADMAP.md)
- [Database plan](docs/DATABASE_PLAN.md)
- [API plan](docs/API_PLAN.md)
- [ML methodology](docs/ML_METHODOLOGY.md)
- [Frozen live feature contract](docs/LIVE_FEATURE_CONTRACT.md)
- [Windows sensor plan](docs/NETWORK_SENSOR_PLAN.md)
- [Security rules](docs/SECURITY_RULES.md)
- [Design system](docs/DESIGN_SYSTEM.md)
- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Architecture review and scope history](docs/ARCHITECTURE_REVIEW.md)
- [Sprint 1 evidence, blockers and next command](docs/SPRINT1_FEASIBILITY_REPORT.md)

## Standalone sensor (PowerShell, Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-sensor.txt
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli capture-interfaces
.\.venv\Scripts\python.exe -m sensor.cli counters --interface "Ethernet 3" --samples 5
.\.venv\Scripts\python.exe -m sensor.cli capture --interface "Ethernet 3" --duration 10
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v
```

Select the actual active interface from enumeration; never assume the example alias remains active. Omit `--samples` for continuous counters; Ctrl+C stops. Counters emit LIVE OS totals, deltas and bytes/second. Capture requires manually installed Npcap and prints LIVE ten-second IP flow summaries with endpoints, ports, directional counts, IP length ranges, timestamps and partial/loss status. Default duration is 10 seconds, maximum 1800. Startup/shutdown windows may be partial. Packet objects are ephemeral; no payloads or capture files are stored. No backend is required.

For an explicitly invoked controlled test, run `.\.venv\Scripts\python.exe tests/sensor/manual_live.py --interface "Ethernet 3"`. It captures for 24 seconds while this laptop sends one public HTTP HEAD request to 1.1.1.1:80 and one DNS query for example.com to 1.1.1.1:53. It verifies matched bidirectional flows, DNS lengths and aggregation conservation. It does not run during unit tests. Private IPs appear in local output; do not commit redirected output. This is a packet-feasibility check, not the complete Sprint 1 gate.

Add `--http-outage` for the Sprint 1 failure fixture: one real health POST to a
reserved non-listening loopback port, 0.2-second socket timeout, explicit failure
and no retries/queue. Controlled TCP/UDP starts after failure while local records
continue flushing to stderr; stdout contains the final JSON result. This is
test-only sink evidence, not a production ingestion or durable delivery client.
