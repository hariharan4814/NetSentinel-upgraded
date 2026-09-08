# Module responsibilities

Modules are domain boundaries, not a requirement for 23 services or Django apps. Proposed Django apps group related concerns; sensor and detection remain separate Python packages.

| Module | Owner/boundary | Responsibility and dependency |
| --- | --- | --- |
| Authentication and RBAC | accounts app | Users, roles, JWT lifecycle; permission checks shared across API/socket access |
| Dashboard | frontend feature | Compose read models; no security inference in UI |
| Network Interfaces | monitoring app + sensor | Interface inventory, capability/status and selected capture scope |
| Real-Time Network Sensor | sensor package | Capture lifecycle, heartbeat, bounded transport and local permissions |
| Device Discovery and Inventory | inventory app + sensor | Passive observations, scoped opt-in probes, identity confidence and address history |
| Traffic and Flow Monitoring | telemetry app + sensor aggregation | Validate/store windows and serve filtered flow metrics |
| Feature Engineering | detection package | Versioned numeric vectors and quality flags from windows |
| ML Model Management | detection_registry app + offline training | Evaluation metadata, trusted artifacts, approval, activation and rollback |
| Anomaly Detection | detection package | Compatible model inference and threshold decisions |
| Threat Analysis | detection rules package | Interpretable behavioural/context evidence; separate from model score |
| Risk Scoring | pure policy functions + incidents app | Versioned device/incident prioritization, component explanations |
| Incident Management | incidents app | Correlation, status transitions, investigation notes and evidence |
| Alerts | incidents app | In-app notifications, cooldowns and delivery/read state |
| Network Health | monitoring app | Interface/sensor health, collection gaps and approved probes |
| Network Topology | inventory read models + frontend | Observed communication edges and confidence, not invented physical links |
| Analytics | analytics app | Mode/time-scoped historical summaries and trends |
| Simulation Lab | labs app + synthetic source | Seeded benign scenarios through shared pipeline; synthetic provenance |
| Replay Lab | labs app + replay source, later | Controlled PCAP/dataset decoding and virtual time |
| Reports | analytics app | Authorized bounded exports with provenance and evidence limitations |
| Audit Logs | audit app | Append-only application events for sensitive changes |
| Settings | configuration app | Validated policy versions, retention, scope and preferences |
| Bluetooth Context | optional adapter, later | Presence/context only, distinct from IP identity and traffic |
| AI Assistant | optional integration, later | Evidence-linked explanations; no authority to classify or execute actions |

## Dependency discipline

Ingestion may call inventory and incident domain services within a transaction. Inventory must not import frontend or capture modules. Detection accepts typed metadata/features/context and returns structured findings without ORM or HTTP dependencies. Replay and simulation implement the same source contract as capture; neither writes directly into incident tables or dashboard stores.

Shared code should be limited to versioned contracts, identifiers, clocks, and small reusable utilities. Avoid a catch-all app or utilities file. Frontend feature boundaries mirror user workflows rather than every database table. Audit recording is invoked by domain services and must not create circular business dependencies.
