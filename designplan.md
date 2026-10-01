# NetSentinel design plan

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
