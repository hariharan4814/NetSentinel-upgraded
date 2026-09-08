# Module responsibilities

Modules are domain boundaries, not 23 services or immediately scaffolded apps. Start with at most six cohesive Django apps as sprints need them: accounts (roles, audit and validated settings submodules), monitoring (sensors, interfaces, host/peer inventory and health), telemetry (samples, flow/features, short history/export), detection_registry (model manifests/assignments), incidents (risk orchestration, workflow/alerts), and labs (run manifests/read views). Sensor and detection are independent Python packages. Split these apps later only for a measured maintenance need; do not build a generic configuration framework first.

The tier definitions in PRODUCT_REQUIREMENTS.md control delivery. This table describes ownership, not authorization to build all features.

| Module | Owner/boundary | Responsibility and dependency |
| --- | --- | --- |
| Authentication and RBAC | accounts app | Users, roles, JWT lifecycle; permission checks shared across API/socket access |
| Dashboard | frontend feature | Compose read models; no security inference in UI |
| Network Interfaces | monitoring app + sensor | MVP: one proven interface with actual counters, capabilities and capture state |
| Real-Time Network Sensor | sensor package | Capture lifecycle, heartbeat, bounded transport and local permissions |
| Device Discovery and Inventory | monitoring inventory submodule + sensor | MVP local host/observed peers; active discovery and per-client attribution experimental |
| Traffic and Flow Monitoring | telemetry app + sensor aggregation | MVP: one-second samples and 10-second flow segments; early retention/budget enforcement |
| Feature Engineering | detection package | MVP host v1 sufficient statistics; remote-device/dataset-transfer schemas experimental |
| ML Model Management | detection_registry app + offline training | Evaluation metadata, trusted artifacts, approval, activation and rollback |
| Anomaly Detection | detection package | Compatible model inference and threshold decisions |
| Threat Analysis | detection rules package | MVP bounded local fan-out rule; backend-history rules advanced; no ML attack classification |
| Risk Scoring | pure policy functions + incidents app | Versioned device/incident prioritization, component explanations |
| Incident Management | incidents app | Correlation, status transitions, investigation notes and evidence |
| Alerts | incidents app | In-app notifications, cooldowns and delivery/read state |
| Network Health | monitoring app | MVP sensor/link state and gaps; approved reachability probes advanced; no general security verdict |
| Network Topology | monitoring read models + frontend | Advanced observed communication graph; React Flow adoption deferred with feature |
| Analytics | telemetry read services | MVP short history; rich summaries/trends advanced |
| Simulation Lab | labs app + synthetic source | MVP local launcher, run selector and deterministic rule incident; UI job launching advanced |
| Replay Lab | labs app + replay source | Advanced PCAP decoding and virtual time; incompatible public CSVs are offline research |
| Reports | telemetry export services | MVP bounded CSV; async/rich reports advanced |
| Audit Logs | accounts audit submodule | MVP append-only application events for sensitive changes |
| Settings | accounts settings submodule | MVP fixed validated policy fields; no generic settings engine |
| Bluetooth Context | optional adapter, later | Presence/context only, distinct from IP identity and traffic |
| AI Assistant | optional integration, later | Evidence-linked explanations; no authority to classify or execute actions |

## Dependency discipline

Ingestion may call monitoring/inventory and incident services within a transaction. Inventory must not import frontend/capture modules. Detection accepts typed metadata/features and locally available bounded context, returning structured findings without ORM/HTTP dependencies. The sensor runs even when detection or HTTP output is unavailable. Simulation and compatible PCAP replay implement the same normalized source contract; neither writes directly into incident tables/dashboard stores. Existing public feature CSVs cannot pretend to implement a packet source.

Shared code should be limited to versioned contracts, identifiers, clocks, and small reusable utilities. Avoid a catch-all app or utilities file. Frontend feature boundaries mirror user workflows rather than every database table. Audit recording is invoked by domain services and must not create circular business dependencies.
