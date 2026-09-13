# Module responsibilities

Sprint 3 adds `frontend/` for presentation and a bounded GET relay only.
It imports neither sensor nor Django code. No Django apps, models or endpoints
change in the initial frontend work. The continuation extends two existing GET
routes for scoped status/session reads using shared bounded read plumbing;
see [FRONTEND_SETUP.md](FRONTEND_SETUP.md) and ADR-024.

Initial Sprint 2 implementation, 2026-09-13: the monitoring app owns sessions and
status; telemetry owns aggregate samples/windows, ingestion and explicit pruning.
These are the only Django domain apps. The user's current task defers all
authentication and extra source/interface/receipt models in the earlier plan.
The sensor package and all Sprint 1 tests remain independent and unchanged.
See [API_PLAN.md](API_PLAN.md) and ADR-023 for the implemented boundary.

Reduced scope accepted 2026-09-11: exactly four product modules. These are cohesive responsibilities, not four microservices or instructions to scaffold everything. Existing sensor code and tests remain the Sprint 1 foundation.

| Core module | Ownership | Responsibility and dependency |
| --- | --- | --- |
| Live Network Monitor | Existing sensor package; future monitoring and telemetry Django apps; Next.js monitor view | Native Windows Npcap/Scapy capture, real one-second counters, packet/protocol/flow aggregation in ten-second windows, interface/sensor status and bounded recent persistence. |
| Anomaly Detection Engine | Reusable detection Python package and offline CLI; small future detection Django app for manifests/results | Genuine baseline, frozen host-v1 inputs, one Isolation Forest, trusted save/load and calibrated Normal / Anomalous output. No ORM or UI dependency in extraction/inference. |
| Explainable Threat Analysis | Pure explanation/rule functions within detection; dashboard finding detail | Compute deviations and bounded rule evidence from observed features/statistics. Store reference values and versions; no LLM, attack certainty, incident lifecycle or weighted risk engine. |
| Network Recovery & Demo Lab | Existing capture supervisor/diagnostic helpers; later isolated simulation/replay sources; monitoring/telemetry read views | Interface loss and explicit gaps, bounded same-identity recovery, new sessions, deterministic labelled demo inputs and compatible replay. No network reconfiguration or synthetic LIVE fallback. |

## Supporting architecture

Start Sprint 2 with only monitoring (source/interface/session/status) and telemetry (samples/flow summaries/ingestion/retention) as cohesive Django apps. Use Django's built-in authentication facilities for a minimal local operator and a scoped machine upload credential as needed; no custom accounts/RBAC framework. Add detection only in Sprint 4 for small model/feature/result records. Lab manifests can live with source sessions; no separate labs app or task service is required.

The Next.js dashboard arrives in Sprint 3. It presents accepted data and explanatory evidence; it neither captures packets nor makes security decisions. Backend authentication, migrations, retention and minimal operational logging are supporting controls, not additional product modules.

## Dependency discipline

Keep capture outside Django request processing. Sensor startup, aggregation and local output require no web framework, database, model or backend connection. An optional bounded HTTP sink cannot stall collection; analysis rejection cannot discard valid telemetry.

Detection accepts typed versioned features, permitted metadata and bounded local context, returning structured results without ORM/HTTP dependencies. Offline training is explicitly invoked. Keep shared code limited to contracts, IDs, clocks and small utilities. Feature/observation/preprocessing/model/rule versions must survive persistence and presentation.

SIMULATION and compatible REPLAY use the shared normalized metadata/aggregation path with isolated mode/run/session and rolling state. Neither writes precomputed findings into the dashboard/database. Public feature tables with different semantics do not implement a packet source. Gap, unknown and partial data never become valid idle values.

## Historical boundaries — OUT OF SCOPE

The former six-app proposal (accounts, monitoring, telemetry, detection_registry, incidents, labs) is superseded; it was never an implemented backend. Do not scaffold incident/alert/risk services, enterprise accounts, broad device inventory, topology, rich reporting, Bluetooth, AI/LLM or intelligence adapters. Advanced RBAC, remote controls/jobs, notifications, multi-model comparisons, microservices and cloud delivery are excluded by [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md). Redis is reserved only for a later demonstrated necessity; Celery is excluded. Historical review evidence remains in [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md).
