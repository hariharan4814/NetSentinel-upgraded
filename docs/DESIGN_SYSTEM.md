# Design system

## Product direction

A professional dark security operations interface with restrained colour, clear hierarchy and readable evidence. Optimize for a student laptop and projector. The dashboard must answer: is the observed network healthy, what is happening now, are there anomalies/incidents, and which device needs attention?

Use Next.js/TypeScript, Tailwind tokens, shadcn/ui, Recharts and TanStack Query for MVP. React Flow accompanies advanced observed topology, not initial scaffolding. These are plans; no components are created in Sprint 0.

## Dashboard and navigation

Persistent header: product/workspace, clearly written LIVE/SIMULATION/REPLAY badge, selected source/interface, last-updated time, connection state and user menu. Mode changes reset mode-scoped queries/subscriptions; never keep a previous mode's results under the new badge. LIVE is not proof of freshness: stale/offline is separately visible.

Add observation coverage: “This laptop / selected interface,” “Interface aggregate — client attribution unavailable,” or validated device scope. Also show capture capability (packet metadata, OS counters only, unavailable), source sample time, and update transport (WebSocket or polling). Mode is independent of capability: OS counters are real LIVE observations but do not support flow/ML panels. SIMULATION/REPLAY selects an explicit run; switching modes never starts/stops capture or changes operator authorization.

First row: sensor/interface health and coverage, current measured throughput, open incidents, and observable subjects needing attention. Main area: traffic chart and incident/recent-flow view. Secondary area: observed endpoints and anomalies when available. Host-only deployments say “This laptop” rather than inventing a network-wide device ranking. Do not say the network is secure/healthy because no incidents exist; packet loss/latency is unavailable unless directly measured by a supported mechanism.

Use accepted one-second samples for visible activity, separate from 10-second finalized flow/detection windows. Label OS interface bytes versus packet IP bytes; do not join them into an apparently equivalent series. Do not redraw random/interpolated values on a timer. If zero anomalies are found, show “No anomalies in evaluated windows” with evaluated-window count, model status and coverage, while rates/flows/history keep updating. If nothing was scored, show ML unavailable/learning instead.

Navigation groups: Overview; Network (interfaces, devices, flows, health, topology); Detection (anomalies, models); Response (incidents, alerts); Analysis (history, reports); Labs (simulation, replay when delivered); Administration (audit, settings, users). Hide unavailable optional features or label them planned without nonfunctional controls.

For MVP, hide advanced topology/replay and remote job controls. The Simulation Lab shows run provenance, actual progress/results and concise local-launch instructions; a local launcher is an explicit MVP workflow. Demonstrate a rule-driven incident with ML disabled without mislabelling its evidence as a learned attack classification.

## Proposed visual tokens

| Token | Starting value/use |
| --- | --- |
| Background | #0B1220 |
| Surface / raised surface | #111C2E / #18263B |
| Main / secondary text | #F1F5F9 / #B8C5D6 |
| Accent/focus | #60A5FA |
| Healthy | #34D399 plus text/icon |
| Warning/anomalous | #FBBF24 plus text/icon |
| High-priority incident | #FB7185 plus text/icon |
| Unknown/stale | #94A3B8 plus explicit timestamp |
| Spacing | 4 px base; 8, 12, 16, 24, 32 px steps |
| Corners/motion | 8–12 px radii; subtle 120–200 ms transitions; respect reduced motion |

Tokens are candidates; measure contrast on final backgrounds. Target WCAG AA contrast and keyboard usability, with visible focus, semantic labels and no colour-only meaning. Use a system sans-serif stack, 16 px default body text and tabular numerals for metrics. Avoid tiny chart labels; enlarge important content for projector use. Do not rely on animation, hover or flashing to convey alerts.

## States, language and evidence

Every data view needs loading, empty, error, stale, partial-coverage and permission-denied states. “No observed traffic” differs from “sensor offline”; “no findings” differs from “model unavailable.” Never convert missing measurements to zero or interpolate across capture gaps without indicating them.

On socket failure show polling mode and refresh every 5 seconds; even a healthy socket reconciles REST at least every 15 seconds. Cancel/ignore responses for previous mode/run/query keys. Backlog uses original observation time, not receipt time, and is labelled delayed; an old batch cannot make the “now” chart look fresh. Counter reset, sleep and interface changes produce gaps/new source epochs. Lab runner absent, model requested-but-not-applied, storage pressure and incomplete windows need distinct states. Alerts never create placeholder data in live charts.

Use anomaly, potentially suspicious, and evidence-supported classification consistently. Incident detail shows observed interval, source/mode, feature deviations, model/threshold, rule evidence, risk components, benign alternatives, coverage and investigation timeline. Risk is a priority score, not a probability. Show proposed operator actions as explicit authorized controls; initial release offers no automatic blocking.

Chart axes state units and time zone; backend UTC is presented in the selected local zone with a clear label. Tooltips are supplemental to readable legends and accessible tabular summaries. Severity and lifecycle use separate badges. Reports include filters, mode, generation time, data freshness and limitations.

Topology shows observed communication relationships, not guaranteed physical wiring. Distinguish inferred/uncertain edges using labels and line styles, cap visible nodes and provide filtering plus a keyboard-accessible table alternative. Responsive layouts stack content and preserve critical status; wide tables may scroll without hiding source/mode labels.
