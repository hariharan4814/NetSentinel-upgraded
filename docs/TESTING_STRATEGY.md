# Testing strategy

This document plans future verification. No tests, environments or application checks were implemented or run in Sprint 0. Keep tests focused on consequential behaviour, independent expectations and failure modes rather than mirroring implementation.

Phase 1B now has 32 sensor unit tests (`python -m unittest discover -s tests/sensor -v`) and an explicitly invoked `tests/sensor/manual_live.py --interface <alias>` hardware check. The latter sends one public HTTP HEAD and one DNS query from the selected local IPv4 address during bounded capture; it is never part of unit discovery. Unit fixtures transmit nothing. Evidence and remaining full-sprint gates are recorded in [SPRINT1_FEASIBILITY_REPORT.md](SPRINT1_FEASIBILITY_REPORT.md).

## Layers and acceptance evidence

| Layer | Critical tests |
| --- | --- |
| Metadata/aggregation unit | Protocol-specific keys, direction, half-open boundaries, timer finalization with no arriving packets, 2-second lateness, idle versus shutdown partial windows, IPv4/IPv6/ICMP/truncation/fragments, sufficient-statistic conservation with drops |
| Feature/ML unit | Host v1 reconstruction parity from stored statistics, byte-layer/flag definitions, idle/missing/incomplete windows, train-only transforms, score direction, threshold boundaries, observation-profile mismatch, deterministic seed and trusted load rejection |
| Rule/risk unit | Benign alternatives, minimum evidence, cooldown, component bounds, missing evidence flags, anomaly-only risk ceiling, no auto-blocking |
| Backend unit/integration | Role/object scope, atomic idempotent ingestion, changed-payload conflict, incident correlation/concurrency, valid transitions, audit attribution and retention snapshots |
| PostgreSQL integration | Real migrations, constraints, query plans, transaction rollback, cleanup and backup/restore; do not rely only on SQLite substitutes |
| REST/WebSocket integration | Authentication expiry/revocation, origin denial, mode-scoped events, post-commit publication, duplicate/missing event recovery and REST reconciliation |
| Sensor integration | Starts with no Django/database/model; one-second sample output; missing driver/privilege, adapter disappearance, sleep/clock/counter reset, idle versus stopped, bounded retry/spool, backend outage, five-second shutdown and no payload retention |
| Frontend workflows | Login, mode switching/cache isolation, stale state, incident review/transition, report access, keyboard focus and reduced motion |
| End-to-end | Real authorized sensor → metadata → database → socket → dashboard with zero anomalies; fixed synthetic metadata → rule → one incident with ML disabled and benign control → none |

## Fixtures and provenance

Use small synthetic metadata fixtures with hand-calculated packet/byte totals and expected features. Keep labels and scenario definitions separate from model inputs. Check exact determinism where feasible and documented numerical tolerance across supported environments. Mode isolation tests must try cross-mode IDs, mixed batches, report filters, model assignment, device identity collisions and socket subscriptions—not only badge rendering.

Verify the ML_METHODOLOGY.md demo contract twice with fresh run state: benign at most three ports yields no incident; two consecutive complete windows of 24 outgoing ports to one peer yield B=1/P=1/risk 55 and exactly one medium SIMULATION incident under the fixed policy with ML disabled. Repeated delivery produces no duplicate alert; incompatible model output does not stop samples/flows. Never preinsert expected incidents or scores. This fixture verifies integration and is excluded from held-out research metrics.

Attribution fixtures must include a gateway MAC serving multiple remote IPs, multiple clients behind one post-NAT address, randomized/changed MACs, and a discovered neighbour with no observed traffic. None should invent a device bandwidth history. API/DB tests enforce subject kinds and mode/run identity. Public dataset promotion tests reject matching column names with incompatible semantics, missing flags or wrong durations; compatible PCAP extraction is an advanced parity test, not an MVP dependency.

Do not commit personal captures or model binaries. Any future sanitized exception requires privacy/license review and narrow ignore-policy adjustment. Replay tests may generate temporary tiny captures from benign fixtures; remove them after use. Maintain fixture manifests identifying origin, seed, expected observation and permitted use. Include scenarios that should produce no incident.

## Research evaluation

Follow ML_METHODOLOGY.md's chronological session splits, calibration/test separation and locked manifests. Compare model-only, rules-only and hybrid on the same observations. Report labelled versus unlabelled results separately, including benign bursts, sparse histories, drift and partial capture. Evaluate alert burden and latency alongside classification metrics; include sample counts and variation, not a single unsupported “accuracy” percentage.

Require explicit evaluation unit, positive-label meaning, ambiguous-window policy, context reset at split boundaries, and duplicate/scenario grouping. Do not report recall on zero positive samples or PR-AUC for a binary-only rule. Estimate variation at session/run level; classify unreviewed live alerts as unreviewed. Record time spent under no-model/incomplete-data conditions rather than treating unscored windows as true negatives. Report synthetic integration success separately from real attack evidence.

## Performance and resilience

Sprint 1 acceptance follows ROADMAP.md's S1-01 through S1-08 exactly: the 30-minute actual-host run, independent console operation, packet/reference checks, privacy, failure bounds and repeatability. Hardware requirements are not satisfied by citations, counters-only fallback, loopback or simulation. Mark unsupported/untested hotspot/monitor mode experimental; they do not block a successful host path.

After integration measure one-second sample-end-to-display latency (p95 under 3 seconds) separately from 10-second-window finalization-to-display latency (p95 under 3 seconds, after the 2-second lateness allowance). A stress experiment at 1,000 packets/s or 50 synthetic subjects does not establish real device visibility. Record actual CPU/RAM/disk, throughput, loss and clean-shutdown delay. Exceed queue/flow/spool caps deliberately and check counted drops and suppressed incomplete-window scoring.

Use 100,000 flow rows for initial query tests, then test near DATABASE_PLAN.md's combined telemetry cap and cleanup threshold with measured row/index/WAL growth. Test age/row/byte limits, status-path availability under storage pressure, retention of incident snapshots, summary correctness and free-space headroom. Document OS disk reuse and restore results; passing a small read test does not validate long retention at maximum flow-key capacity.

Inject backend outage, socket disconnect, process restart, disk pressure, malformed batches, invalid models, old timestamps, counter resets, sleep/resume and permission revocation. Verify two-stream retries preserve valid telemetry, delayed batches do not fire current alerts, desired models remain pending until actual acknowledgment, and capture continues locally with an unavailable backend/model. Stop the only final socket notification and verify 15-second reconciliation; verify 5-second polling fallback. Test HTTP ingestion and sockets in the same ASGI process; never use external group_send with the in-memory layer. A later multiworker deployment needs a supported shared layer and cross-process tests.

## Security and manual checks

Test expired/replayed tokens/tickets, ticket-query redaction, CSRF-sensitive operations, auth/session-version revocation including socket recheck bounds, object-ID substitution, viewer writes/detailed-data access, sensor privilege escalation, path traversal, parser quotas, CSV injection, UI escaping and secret redaction. Inspect storage/log/spool/library temporary outputs for payload retention. Confirm local versus backend capture authority is disclosed; backend revocation cannot promise immediate offline shutdown. Scan dependencies/secrets when implementation exists.

Manual Windows evidence is required for each supported capture configuration: OS/adapter/driver versions, privilege setup, hotspot result, reference traffic and observed limitation. Perform keyboard, screen-reader spot checks, responsive layout and projector review on primary workflows. Hardware-dependent tests may be opt-in in CI but must have recorded manual results for release claims.

## Delivery gates

Each implementation sprint supplies relevant tests, migration checks where applicable, a reproducible run procedure and honest limitations. Future CI should run lint/type checks and fast backend/detection tests per change, plus PostgreSQL integration and production frontend build before release. Run hardware/long performance tests at relevant milestones rather than on every documentation edit.

Final submission requires a clean-start demonstration, backup/restore evidence, actual live observations with useful zero-anomaly UI, separately labelled deterministic rule simulation, and honest measured research results. Advanced topology/replay/AI/hotspot support is not required. Report unsupported capabilities and failed experiments. Sprint 0 review validation is limited to documentation completeness/consistency, links, diff/content review and absence of application scaffolding; it cannot establish actual hardware support or runtime performance.
