# NetSentinel

**NetSentinel: An Intelligent Real-Time Network Monitoring, Anomaly Detection and Cybersecurity Incident Response System**

A final-year M.Sc Computer Science project to observe network metadata on a Windows laptop, build behavioural baselines, identify unusual activity, and support evidence-based incident investigation through a web dashboard.

**Status: Sprint 0 — planning foundation only.** There is no runnable application, installed project environment, or implemented detection capability yet.

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

Start with the roadmap's exact Windows feasibility gates when implementation is authorized. Full Wi-Fi visibility, Mobile Hotspot traffic attribution and per-remote-device models are experimental. The MVP is host monitoring, transparent detection, basic investigation and a labelled demonstration; advanced features cannot delay final evaluation. No installation or run commands are provided because implementation has not started.
