# Public measurements and reports

Updated 2026-10-02. These are public-browser tools. They never contact the local
companion, Django, packet sensor, Windows security APIs or a privileged broker.
The existing eight-request lightweight connection check is retained separately.

## Speed test contract

`frontend/src/lib/public-measurements.ts` dynamically imports the pinned
`@cloudflare/speedtest` 1.14.1 engine after an explicit consent checkbox and Start.
The official engine documents its public Cloudflare edge measurement endpoints:
<https://github.com/cloudflare/speedtest>. Only fixed HTTPS `__down` and `__up`
endpoints are configured; arbitrary target URLs are not accepted.

- Six unloaded HTTP latency samples; download requests of 1 MB and two 5 MB;
  upload requests of 0.5 MB and two 2 MB. The engine can stop a direction early
  after a request takes at least 1,000 ms. Planned payload maximum 15.5 MB.
- Engine 1.14.1 retries HTTP 429 up to three times. The worst configured attempted
  payload budget is therefore 62 MB, plus request/response protocol overhead and
  retransmissions. This is disclosed before consent, not described as a 15.5 MB
  unconditional cap. No application-level retry is added.
- Global 45-second deadline and engine 12-second request abort. Cancel, navigation
  away and tab hiding call `pause()`, which aborts the current engine fetch.
  No background testing. UI cooldown is one minute; this is courteous client-side
  throttling, not a security or provider quota guarantee.
- Packet loss, TURN, RPKI, loaded latency, result logging and measurement logging
  are disabled. Credentials are omitted. Browser/platform scheduling can delay
  a timeout callback; the nominal deadline is not a real-time OS guarantee.
- Progress is the actual engine phase plus completed sample count. No invented
  percent or estimated line capacity.

Download throughput accepts only engine samples whose requested body length
matches an observed Resource Timing `decodedBodySize`. Missing CORS timing or a
mismatched body yields unavailable, never assumed bytes. Mbps is sum(payload
bytes * 8) / sum(valid measured duration ms) / 1,000. Samples shorter than 10 ms
are excluded. Upload throughput uses completed request-body bytes and the
engine's measured upload duration. The engine's duration includes its documented
server-time correction; NetSentinel does not use its estimated 0.5% wire overhead
as measured payload. This remains a short single-connection HTTP measurement,
not the maximum capacity of a line. Fast links can be understated.

Latency is median successful unloaded HTTP sample time in ms. Jitter is
`sum(abs(sample[i] - sample[i-1])) / (n-1)` for n >= 2. It is unavailable with
fewer samples. This is not ICMP ping or packet loss.

Data accounting separately shows actual browser-reported received response-body
bytes and payload bytes for completed upload responses. Missing timing is null.
Failed/cancelled/timeout tests are explicitly partial; unfinished uploads and
failed or retried requests may consume additional bytes. Neither counter includes
all wire headers or retransmissions, and neither is ISP billable data. Only
complete runs are eligible for history; partial observations remain in the tab.

Cloudflare's maintained open-source engine explicitly documents external use of
its measurement endpoints. The MIT software license is not an uptime or free
bandwidth guarantee. Review [Cloudflare terms](https://www.cloudflare.com/website-terms/)
and [privacy](https://www.cloudflare.com/privacypolicy/) before broad promotion.
The UI discloses the external service and data cost. HTTP 429/error/CORS failures
stay failures. No paid account, key or paid infrastructure was provisioned.

## Optional public IP lookup

An explicit user action makes one browser-side request to
`https://ipwho.is/?fields=success,ip,type,city,region,country,connection`.
No cloud-server outbound-IP inference, proxy, forwarded header or client key is
used. HTTPS, credentials omitted, redirects rejected, 8-second timeout, 16 KiB
response cap. No automatic retry. A one-minute UI cooldown avoids repeated clicks.

The [provider documentation](https://ipwhois.io/documentation) reviewed on
2026-10-02 describes free CORS access, IPv4/IPv6, no API key, and a 1,000/day
limit **shared by all requests from a website domain**. [Pricing](https://ipwhois.io/pricing)
and [terms](https://ipwhois.io/terms) allow free commercial use subject to fair
use, with no uptime SLA. These are provider service terms, not an open-source
license. [Privacy disclosure](https://ipwhois.io/privacy) is linked beside consent.
Do not build a general-purpose IP database/export service from this integration.

Only the visitor's own current lookup is exposed; arbitrary IP lookup is absent.
Returned IP, family, ASN, organization and approximate city/region/country are
allowlisted. Coordinates, abuse labels and other fields are dropped. Missing
fields remain unavailable. VPN/proxy/shared routing and outdated geolocation are
explicit limitations. One successful lookup may expose only one address family;
the other remains not observed. Disable & clear cancels and removes tab data.
Nothing from the lookup goes into browser history automatically.

Alternatives considered: ipapi.co now advertises a limited trial; ipapi.is has
restrictions around public data export. Neither was selected. Service availability,
CORS and shared daily budget must be checked again before final deployment; mock
tests do not establish live endpoint permission or availability.

## History, PDF and privacy

Speed history is off by default, at most 30 completed tests for 30 days under
`netsentinel.speed-history.v1`. It stores no IP/location/executable identity.
Loads and writes revalidate, strip unknown fields, deduplicate, expire and bound
records. Disable deletes saved speed results. Existing HTTP history retains its
separate 10-check/7-day contract. Storage failures preserve in-tab results and
explain browser site-data deletion. Anyone using a browser profile can see its
saved results. There is no cross-device synchronization.

PDF generation uses pinned jsPDF 4.2.1 and AutoTable 5.0.8, dynamically loaded on
request. User chooses public sections and UTC date range. The current record and
retained records are deduplicated. Available network details are excluded unless
selected; IP and location are separately hidden by default. No lookup or speed
test is triggered by export. Local security/application sections cannot be
fabricated from public data. Tables are selectable text with repeated headers,
page numbers and proper pagination; throughput bars are vector graphics.
No HTML-to-PDF, screenshot, PDF JavaScript, embedded attachments or remote images.
Built-in fonts transliterate Latin accents and replace unsupported characters
with `?`; this explicit limitation avoids broken glyphs. Unicode font embedding
is a future improvement before non-Latin report names are promised.

Reproduce the labelled, non-private sample:

```powershell
cd frontend
npx tsx scripts/create-public-report-example.ts
```

It writes `docs/examples/public-report-simulation.pdf`, labelled SIMULATION on
every page. Its reserved documentation IP is redacted by default. Synthetic
fixtures never seed application state. See root plan for actual rendered-PDF QA.

## Public release boundary

The source allowlist adds only public UI/helpers, the release metadata manifest
and third-party notices. It still excludes `/local`, APIs, the companion, sensor,
database, environment and private configuration. `companion-release.json` starts
with `available:false`. A download link appears only for a verified asset under
the project's exact GitHub releases URL. Root release work owns publication and
manifest activation. Do not mark the installer available because its code exists.

## Verification commands

```powershell
cd frontend
npm run typecheck
npm run lint
npm test
npm run build
npm run test:e2e
npm audit
```

Public browser tests use clearly controlled endpoint fixtures, exercise explicit
consent, real engine completion against those fixtures, history, endpoint failure,
lookup limits, mobile PDF download/redaction and unpublished-companion state.
Live external validation and deployed primary-flow checks belong in release QA.

## Evidence recorded 2026-10-02

- `npm run typecheck` and `npm run lint`: pass after fixing strict engine callback
  typing and lazy React date initialization.
- `npm test`: 52 passed, zero failed, including the local-auth tests being added
  in the same upgrade and nine new public measurement/report tests. The restricted
  shell initially failed in tsx with `uv_os_get_passwd ENOMEM`; the authorized
  ordinary host test invocation passed. This was a runtime permission limitation,
  not a skipped test or changed assertion.
- `npm audit --audit-level=low`: zero reported vulnerabilities after compatible
  patches. No framework major-version replacement.
- The five-page PDF sample was rendered through bundled Poppler and every page
  visually inspected: repeated table headers, long organization wrapping, labels,
  bar chart, margins and page numbers are legible without overlap. Poppler emitted
  missing optional Symbol/ArialUnicode display-font warnings; the used Helvetica
  text rendered correctly. The unavailable pdftotext executable was replaced by
  bundled pypdf text extraction. All five pages contain SIMULATION; reserved test
  IP and location are absent; the long organization text is preserved.
- Rendered QA images are in ignored `tmp/pdfs/public-report-simulation-1.png`
  through `-5.png`. Final non-private sample is `docs/examples/public-report-simulation.pdf`.
- Combined production build and browser tests are coordinated by the integration
  agent; consult root `plan.md` for their later results. These unit/PDF checks do
  not claim a live external test or deployed-site verification.
