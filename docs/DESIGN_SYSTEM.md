# Design system

## AI Lab implementation — 2026-10-06

`/lab` uses scoped vanilla CSS: a deep teal navigation rail, cool translucent
panels, readable system fonts and explicit SIMULATION badges. The page follows
scenario studio → retained experiments → computed evidence → how-to. The rail
becomes compact navigation below 760px; forms and evidence panels stack, and
wide numeric tables scroll within labelled keyboard-focusable regions.

States include sign-in, loading, empty store, queued/running/cancellation,
failed jobs, unscored observations, disconnected backend and retained historical
results. No illustrative metrics populate empty states. Playback shows recorded
test windows, never live traffic; generated truth is an explicit overlay.
The evidence view presents actual metrics and SHAP output with limitations.
PDFs contain semantic tables and charts with pagination, not UI screenshots.
This scope supersedes the historical prohibition on lab job controls below.

Automated 360px overflow checks and production browser workflow checks passed
on 2026-10-06. Visual and rendered-PDF review evidence belongs in `plan.md`.

## Current public design — 2026-10-01

The public connection helper follows ../designplan.md: vanilla CSS, deep teal
sidebar, translucent cool-white surfaces, system fonts, responsive navigation,
real measurement states and accessible text alternatives for charts. No external
font request, UI library or decorative fake telemetry is introduced. The original
technical stylesheet stays with `/local`. Earlier tokens/plans below are historical
and do not override the public design plan.

Sprint 3 implementation uses the dark tokens below with responsive plain CSS,
system fonts and accessible HTML tables. One page has five monitor sections;
no future ML navigation is scaffolded. Charts show separate measured points,
not lines through missing intervals. Capture/gap data unavailable from the API
stays explicitly unavailable. The continuation displays stored capture events,
gaps and session metadata; a stale report is historical, and physical interface
link state remains unavailable. See [frontend setup](FRONTEND_SETUP.md).
This current authorization supersedes the earlier setup prohibition below.

## Product direction

A simple professional dashboard for a Windows student laptop and projector. Answer: what traffic is observable now, is the selected interface being monitored, which complete windows are unusual, and what observed evidence explains them? An anomaly is not an attack; no findings is not a secure-network verdict.

Planned Sprint 3 stack: Next.js/TypeScript, Tailwind, shadcn/ui, Recharts and TanStack Query where useful. No frontend setup is authorized by this cleanup. React Flow/topology and enterprise response screens are OUT OF SCOPE.

## Four module views

| View | Content |
| --- | --- |
| Live Network Monitor | Upload/download, packet counts, TCP/UDP/protocol mix, active flow keys for a stated ten-second window, interface/sensor status, traffic chart and bounded recent flow table. |
| Anomaly Detection Engine | Normal / Anomalous for scored windows, unusualness score/threshold, actual model version, evaluated-window count and availability/coverage. |
| Explainable Threat Analysis | Observed feature/statistic, units, reference range or threshold, deviation, interval, rule/reference version and benign alternatives. No risk dial, attack probability or incident workflow. |
| Network Recovery & Demo Lab | Loss/recovery status, visible gap intervals, selected interface identity, labelled SIMULATION/REPLAY run selector, local launch instructions and computed scenario results. |

Use a compact navigation with these four views; interface/flow details can be sections of the monitor. Add only minimal operator/session controls. Do not reserve menu placeholders for removed enterprise features. REPLAY is visibly unavailable until a compatible source is implemented; selecting a mode never starts/stops capture.

Persistent header: project name, explicit LIVE / SIMULATION / REPLAY badge, selected source/interface or lab run, observation coverage, last-observed time and current connection state. LIVE is provenance, not freshness. Mode changes reset/partition query caches and ignore old responses.

First row: current upload/download, packets, TCP/UDP and observed active flows; nearby show capture/interface status and coverage. Main area: measured traffic chart plus recent flows. Later analysis panels cannot displace useful monitoring when there are no anomalies or no model. Flow segments are not proven established TCP connections or remote monitored devices.

## Measurement and state language

Label "This laptop / selected interface" or "Interface aggregate; client attribution unavailable" according to actual evidence. Show PACKET_METADATA, OS_COUNTERS_ONLY or unavailable capability. OS counters support real rates but cannot fabricate protocols, flows or ML. Separate OS bytes from packet IP bytes; never sum or splice them into one apparently equivalent series.

Use actual one-second samples and independently finalized ten-second analysis windows. Show units and observed timestamps. Missing observations, interface loss and recovery intervals are chart gaps, not zeros or interpolated traffic. Preserve partial/stale/delayed states; a newly received historical batch cannot make "now" fresh.

All views need loading, empty, error, stale, partial and permission-denied states. "No observed traffic" requires valid active coverage. "No anomalies in evaluated windows" includes the evaluated count and model status; nothing scored shows "ML unavailable" or "Baseline collection," not Normal.

Show RUNNING, INTERFACE_LOST, RECOVERING and STOPPED with explicit reasons, detected gap duration and source/session change. Recovery does not claim continuous coverage. An unexpected native termination cannot be described as a safe recovery success without evidence.

REST polling initially refreshes bounded latest data about once per second on the active page, avoids overlapping requests and backs off on failure. Display actual freshness, refresh after reconnect, and cancel previous mode/run requests. Add WebSocket transport only after measured need and the authorization/reconciliation rules in API_PLAN.md.

## Explanations and demo

Use concrete wording: "24 outgoing destination ports observed; demonstration threshold 20" or "Packet rate above this baseline range." Explain limitations and benign bursts. Do not claim malware, attack, exfiltration or port scan from the model alone; even tentative language requires supporting observations.

The deterministic SIMULATION demo computes two qualifying window findings and zero benign-control findings under ML_METHODOLOGY.md. ML may be unavailable. Mode/run/source and generated nature remain visible on every result and screenshot. No hardcoded scores/findings or LLM explanations. Replay uses original event time with processing time separately shown.

## Proposed visual tokens

| Token | Starting value/use |
| --- | --- |
| Background | #0B1220 |
| Surface / raised surface | #111C2E / #18263B |
| Main / secondary text | #F1F5F9 / #B8C5D6 |
| Accent/focus | #60A5FA |
| Running / valid observed state | #34D399 plus text/icon |
| Anomalous / warning | #FBBF24 plus text/icon |
| Capture error / loss | #FB7185 plus text/icon |
| Unknown/stale | #94A3B8 plus explicit timestamp |
| Spacing | 4 px base; 8, 12, 16, 24, 32 px steps |
| Corners/motion | 8–12 px radii; subtle 120–200 ms transitions; respect reduced motion |

Tokens remain candidates: measure contrast on rendered backgrounds and target WCAG AA. Use visible keyboard focus, semantic labels, a system sans-serif stack, 16 px default text and tabular numerals. No colour-only state, tiny chart labels or hover-only essential information.

Charts label units/time zone; store UTC and show the selected display zone explicitly. Provide accessible table summaries. Responsive layouts stack cards and allow wide flow tables to scroll while retaining source/mode labels. Redact private metadata in academic screenshots and report examples.

## OUT OF SCOPE navigation

No devices/inventory ranking, topology, incident assignment/triage/resolution, enterprise alerts/notifications, user-role administration, generic policy/audit consoles, report-job system, Bluetooth, intelligence API, AI chatbot or remote capture/job-control screens. Recent traffic history and final academic report/screenshots remain part of the core project.
