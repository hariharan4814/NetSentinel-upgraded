# NetSentinel

**NetSentinel: An Intelligent Real-Time Network Monitoring, Anomaly Detection and Cybersecurity Incident Response System**

A final-year M.Sc Computer Science project to observe network metadata on a Windows laptop, build behavioural baselines, identify unusual activity, and support evidence-based incident investigation through a web dashboard.

**Status: Sprint 1 Phase 1B — real packet capture demonstrated.** Npcap/Scapy captured controlled bidirectional TCP and UDP on the laptop's USB network interface and produced bounded flow summaries. Full Sprint 1 is PARTIALLY PASSED: sustained resource, reference and feature-contract gates remain. There is no web application or detection capability.

## Intended system

Windows interface → local Python sensor → flow aggregation → feature extraction → Isolation Forest and threat analysis → Django → PostgreSQL → Channels/WebSocket → Next.js.

The initial live unit of observation is the laptop/selected interface, not every Wi-Fi device. The independently runnable sensor also emits real one-second interface samples for visible activity while ten-second behavioural windows close. Missing models or zero anomalies do not stop monitoring. Packet-capture failure can retain clearly labelled OS-counter monitoring, but counters alone do not fulfill the live flow/ML requirement.

The browser presents data; it never captures network traffic. Isolation Forest identifies unusual behaviour, not attack types. Anomalous, potentially suspicious, and evidence-supported classifications remain distinct.

LIVE uses actual observable metadata. SIMULATION uses clearly labelled synthetic scenarios, including a deterministic rule-based investigation demonstration independent of ML output. REPLAY is advanced: compatible PCAP metadata can use the shared pipeline; incompatible public feature tables remain separate offline experiments. Every record, chart, event, and report retains its mode and source session.

## Planned stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui, Recharts, React Flow, TanStack Query |
| Backend | Django, Django REST Framework, SimpleJWT, Django Channels |
| Persistence | PostgreSQL |
| Sensor and detection | Python, Npcap where required, Scapy and/or PyShark, psutil, NumPy, Pandas, scikit-learn, joblib |
| Deferred | Redis only with a justified deployment change; Celery is outside the native-Windows MVP; threat intelligence, Bluetooth context, LLM integration |

## Planning documents

- [Agent instructions](AGENTS.md)
- [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Module responsibilities](docs/MODULES.md)
- [Sequential roadmap](docs/ROADMAP.md)
- [Database plan](docs/DATABASE_PLAN.md)
- [REST and WebSocket plan](docs/API_PLAN.md)
- [ML methodology](docs/ML_METHODOLOGY.md)
- [Windows sensor plan](docs/NETWORK_SENSOR_PLAN.md)
- [Security rules](docs/SECURITY_RULES.md)
- [Design system](docs/DESIGN_SYSTEM.md)
- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Strict architecture and feasibility review](docs/ARCHITECTURE_REVIEW.md)

Full Wi-Fi visibility, Mobile Hotspot traffic attribution and per-remote-device models remain experimental. See the [Sprint 1 evidence and limitations](docs/SPRINT1_FEASIBILITY_REPORT.md).

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
