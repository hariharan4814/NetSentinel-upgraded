# NetSentinel agent instructions

## Current stage

Sprint 0 is documentation only. Do not create application code, environments, dependency manifests, Docker files, or generated scaffolds unless a subsequent user task explicitly authorizes implementation. A roadmap entry is not authorization to execute it.

## Read before changing anything

Read [README.md](README.md), [product requirements](docs/PRODUCT_REQUIREMENTS.md), [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), and [security rules](docs/SECURITY_RULES.md). Inspect repository status and any more specific AGENTS.md instructions. Then read the relevant documents:

| Work | Required additional reading |
| --- | --- |
| Backend or domain boundaries | MODULES.md, DATABASE_PLAN.md, API_PLAN.md |
| Sensor or discovery | NETWORK_SENSOR_PLAN.md, ML_METHODOLOGY.md, API_PLAN.md |
| ML, rules, scoring | ML_METHODOLOGY.md, DATABASE_PLAN.md, TESTING_STRATEGY.md |
| Frontend, analytics, topology | DESIGN_SYSTEM.md, API_PLAN.md, MODULES.md |
| Any implementation | TESTING_STRATEGY.md and the applicable sprint acceptance gate |

All documents above are under docs/. Update affected contracts and decisions with the implementation; do not silently contradict them. Document new architectural decisions in the decision register in ARCHITECTURE.md, including reasons, consequences, and status. Label assumptions and proposed thresholds as such.

## Non-negotiable engineering rules

- An anomaly is not an attack. Isolation Forest detects unusual behaviour; rules and corroborating evidence interpret it. Never present its score as an attack probability.
- Preserve LIVE, SIMULATION, or REPLAY provenance end to end. Never fill live views with demo values or mix synthetic training records into a live baseline implicitly.
- Browsers do not capture packets. Keep capture outside Django request processing, and detection independent of presentation and Django models.
- Use modular Python packages and multiple cohesive Django apps. Avoid unnecessary microservices and premature Redis/Celery adoption.
- Prefer metadata and aggregates. Do not persist payloads by default. Never commit captures, credentials, private datasets, model artifacts, or personal network inventories.
- Enforce authorization server-side for REST, WebSockets, reports, sensor enrollment, capture controls, and model activation. No automatic blocking based on an anomaly.
- Use environment variables for secrets, migrations for schema changes, bounded buffers, explicit failures, UTC storage, and versioned ingestion/features/models/rules.
- Preserve user work. Make only requested changes. Test important backend, ML, security, and provenance behaviour; report checks actually run and limitations.
- Keep Windows and a student laptop as the reference environment. Select and pin compatible versions during the authorized setup sprint, not by guessing now.

## Completion reporting

State what changed, why, validation results, and remaining risks. Do not claim a capability, accuracy result, live capture, or test success that has not been demonstrated. Follow the user's current scope over this planning baseline.
