# NetSentinel

**NetSentinel: An Intelligent Real-Time Network Monitoring, Anomaly Detection and Cybersecurity Incident Response System**

A final-year M.Sc Computer Science project to observe network metadata on a Windows laptop, build behavioural baselines, identify unusual activity, and support evidence-based incident investigation through a web dashboard.

**Status: Sprint 0 — planning foundation only.** There is no runnable application, installed project environment, or implemented detection capability yet.

## Intended system

Windows interface → local Python sensor → flow aggregation → feature extraction → Isolation Forest and threat analysis → Django → PostgreSQL → Channels/WebSocket → Next.js.

The browser presents data; it never captures network traffic. Isolation Forest identifies unusual behaviour, not attack types. Anomalous, potentially suspicious, and evidence-supported classifications remain distinct.

LIVE uses actual observable metadata. SIMULATION uses clearly labelled synthetic scenarios. REPLAY will process PCAP/datasets through the shared pipeline. Every record, chart, event, and report retains its mode and source session.

## Planned stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui, Recharts, React Flow, TanStack Query |
| Backend | Django, Django REST Framework, SimpleJWT, Django Channels |
| Persistence | PostgreSQL |
| Sensor and detection | Python, Npcap where required, Scapy and/or PyShark, psutil, NumPy, Pandas, scikit-learn, joblib |
| Deferred | Redis when cross-process messaging requires it; Celery when durable job needs justify it; threat intelligence, Bluetooth context, LLM integration |

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

Start with the roadmap's Windows feasibility gate when implementation is authorized. Full Wi-Fi visibility and hotspot client attribution are unproven; local observation is the minimum live scope. No installation or run commands are provided because implementation has not started.
