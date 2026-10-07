# NetSentinel design plan

## Active direction: AI experiment workbench — 2026-10-04

**Design proposal, not implemented.** Follow the active AI Lab section in
[plan.md](plan.md). Preserve the existing public utility and companion designs
below; the new primary academic experience is an authenticated local `/lab`.

### Purpose and visual direction

Make the project understandable as an experiment: **create traffic, train a
model, test it, understand its mistakes**. Use vanilla CSS, restrained
glassmorphism and readable scientific charts. Visual complexity should come
from useful evidence, not animated fake packets, random counters or invented
security scores. Keep original connection tools in a separate Tools destination.

Retain the existing teal/mist palette, Segoe UI/system fonts, spacing scale and
rounded panels. Use translucent surfaces for navigation and major cards with an
opaque fallback; use solid chart/table backgrounds for contrast. Avoid blur on
every row, heavy gradients under text, external fonts or a new UI framework.
Light mode is the first complete theme; a second theme is optional after QA.

### Information architecture and screen requirements

| Screen | Main action | Required evidence and states |
| --- | --- | --- |
| Lab overview | Start guided experiment / resume saved run | Plain-language problem, workflow, most recent actual experiment; empty state if none |
| Scenario Studio | Generate preview, then dataset | Presets, seed, workload mix, bounded intensity, virtual duration, computed timeline/map, event budget, cancellation |
| Training Lab | Train selected model | Dataset quality, run-group split, feature schema, model choice, bounded settings, actual job stages, success/failure/cancelled |
| Detection Console | Play / pause / step / compare | Selected model, virtual event time, wall time, feature/anomaly series, unscored intervals, observed-pattern evidence |
| Explain & Compare | Inspect prediction / rerun a what-if | Learned reference or SHAP contributions, output meaning, alternate benign reason, baseline comparison, mistakes |
| Reports & Viva | Export selected experiment | Period, provenance, frozen metrics, versions/seeds, charts/tables, redaction defaults, report preview |
| How it works | Follow a five-step tutorial | What problem this solves, what is simulated, what ML computes, how to interpret errors and rerun an experiment |

The optional AI assistant is a collapsible explanation panel inside an
experiment, not the central product. Show the local model name and source
references. No runtime means “AI assistant not set up”; a deterministic summary
must be labelled as such. It does not control the OS or execute user instructions.

### A clear first demonstration

1. Welcome explains the research problem and offers a named synthetic preset.
2. A compact scenario form shows seed and virtual duration before generation.
3. The generated dataset preview shows actual sample counts, quality and splits.
4. Training shows real stages. During estimator fitting use an indeterminate
   indicator, not fake percentages or invented epochs.
5. Results show computed predictions first. “Reveal injected scenario” toggles
   the ground-truth layer without changing predictions.
6. The explanation drawer connects a chart point to exact feature values,
   learned reference, model version and uncertainty.
7. Comparison includes the legitimate high-volume case and any false alert.
8. Export creates a semantic PDF with the same saved results and clear scope.

Use a guided path for beginners and an expandable advanced section for model/
scenario parameters. Controls unavailable at a stage explain the missing
prerequisite. Every visible button must perform a real action or state why it
cannot yet do so; do not ship decorative “Train AI” or “Block attack” controls.

### Persistent scientific context

- Top ribbon: **SIMULATION · no network packets sent**, run name, model version,
  dataset/split version and save state. Keep LIVE/REPLAY visibly distinct in
  their separate existing experiences.
- Playback of a saved synthetic run says “Recorded simulation”; the generated
  source remains SIMULATION. Do not label it live monitoring.
- Use “Within baseline”, “Anomalous” and “Unscored”, never “Your network is safe”.
  Show behaviour-family prediction separately from injected challenge truth.
- Define Mbps/bytes, seconds, event-time windows, class support and score meaning
  near charts. Do not label classifier output as attack probability.
- Labels or icons accompany colour: teal for ordinary activity, amber for
  unusual patterns, muted grey for unavailable data, coral for execution errors
  or explicitly injected challenges. A red colour is not proof of compromise.
- A topology is a **virtual scenario map** generated from flow records. It is
  not a discovered inventory of the user's router or surrounding devices.

### Charts, accessibility and performance

Use existing React capabilities with semantic HTML/SVG and modest vanilla CSS.
Select a maintained chart component only if the needed interactions justify it;
record its license and pin it then. Provide data tables for charts, keyboard
navigation, visible focus and textual labels for confusion-matrix cells.

Desktop uses a narrow sidebar and a flexible work area. The scenario/config
panel can sit beside a larger timeline; training/comparison uses aligned cards.
At mobile widths stack controls and evidence, keep touch targets at least 44px,
and permit only deliberately labelled table containers to scroll horizontally.
Test 360px, 768px and desktop layouts plus 200% zoom. Aim for WCAG AA contrast,
support reduced motion, and avoid colour-only distinctions or auto-playing
packet animations. Announce stage changes without flooding screen readers.

Bound visible timeline points/rows, paginate long results and retain full numeric
data for export within the experiment limits. Decimate chart rendering only;
never silently decimate the evaluation dataset. Keep controls responsive while
training occurs in the worker. Polling reflects server state, not browser guesses.

### Design acceptance checklist

- [ ] A novice can explain the purpose and finish a guided seeded experiment.
- [ ] All charts, predictions and reports come from recorded computed results.
- [ ] SIMULATION, virtual time, missing data and uncertainty stay visible.
- [ ] Empty, training, failed, cancelled, disconnected and no-model states work.
- [ ] Keyboard/mobile/zoom/reduced-motion checks pass with recorded evidence.
- [ ] PDF labels, pagination and redaction match the saved experiment.
- [ ] Public utility and `/local` remain usable; `/lab` stays out of public export.

No visual implementation or browser verification was performed for this planning
checkpoint. See A6/A7/A8 in `plan.md` for execution and acceptance tracking.

---

## Preserved public-utility design (2026-10-01)

Prepared before implementation, 2026-10-01.

## Visual thesis

A calm, precise connection workspace: deep teal navigation, a cool mist canvas,
translucent glass panels and a distinctive circular connection-check control.
Everyday language and a clear next action take priority over technical density.
Use handwritten vanilla CSS with no Tailwind, shadcn or new animation package.

## Layout and information architecture

- Desktop: narrow persistent sidebar, flexible main workspace, compact top bar.
- Navigation: Overview, Fix a problem, Recent checks, Download planner, How it
  works. Every destination contains working controls or useful content.
- First viewport: short purpose statement, prominent Run connection check,
  explicit “not checked” state, metric placeholders and quick symptom choices.
- Overview: check status and circular progress control, three metric cards,
  response chart with accessible individual readings, recommended next step.
- No fabricated default statistics, pretend “connected” status or fake devices.
- Mobile: branding and horizontally scrollable navigation; single-column cards,
  full-width main action, readable chart and no body-level horizontal scrolling.

## Tokens

| Purpose | Value |
| --- | --- |
| Canvas | #edf4f3 with restrained cyan/blue radial light |
| Navigation | #102e32 |
| Main ink | #163438 |
| Secondary ink | #50686b |
| Accent | #087d72 |
| Accent wash | #d9eeea |
| Glass surface | rgba(255,255,255,.78) |
| Border | rgba(255,255,255,.9), subtle teal separators |
| Warning | #865313 on #fff1db |
| Radius | 16px panels, 10px controls, pill status labels |
| Shadow | large, low-opacity blue/teal ambient shadow |
| Spacing | 4, 8, 12, 16, 24, 32, 40px |

Glass appears on major surfaces with a solid fallback and limited backdrop blur.
Text must remain readable without blur. Do not put text over decorative imagery.
Use system sans-serif fonts (Segoe UI on Windows), strong headings and tabular
numbers. Main copy 16px; controls/labels >=14px; metadata >=12px.

## Components and interaction

- Small consistent inline SVG line icons; decorative icons hidden from AT.
- Circle shows an initial check symbol, progress count while running and result
  count afterward. The circle is a real action, not a mock speedometer.
- Metrics: typical HTTP response, response range, requests answered. Units and
  scope always accompany the values. Missing results use an em dash, never zero.
- Chart: actual independent response points, failures represented explicitly,
  no interpolation through gaps. Table/list of individual measurements available.
- Guided fixes: symptom selection, small ordered checklist, completion state,
  reset and suggestion to run a new check after one change.
- History: timestamp, scope, results, before/after comparison and individual/all
  deletion. Support report contains method and limits in plain text.
- Planner: labelled file size/unit and manually entered Mbps; result explicitly
  theoretical with overhead/congestion caveat.
- Guide: three-step getting started, measurement explanation, privacy, FAQ and
  link to trustworthy troubleshooting documentation.

## States

Design idle, checking, cancelled, complete, partial failures, all failures,
localhost scope, storage unavailable, no history and invalid calculator inputs.
Use text plus icon/color. A successful check is not a universal health verdict.
Do not show cancelled results as complete. Navigation during a check cancels it.

## Accessibility and quality

Use semantic landmarks/headings, buttons for actions, labelled form inputs,
visible focus rings, a skip link, polite status announcements and text alternatives
for charts. Use 44px touch targets and respect prefers-reduced-motion. Keep hover
transitions <=180ms; no automatic looping decorative animation. Check desktop,
390px mobile, keyboard navigation, reduced motion and 200% text usability.

## Legacy presentation

Keep the original technical dashboard at /local with its own stylesheet. Exclude
that route from the public static build. No unrelated sensor or ML UI rewrite is
needed for this product direction.
