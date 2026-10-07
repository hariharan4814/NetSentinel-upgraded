# Open-source and external service register

Reviewed 2026-10-02 for the Windows-companion/public-tools upgrade. This document
records public frontend additions; existing Python/Windows components and their
packaging obligations are documented in the companion release instructions.

| Component | Version | Purpose | License / redistribution |
| --- | --- | --- | --- |
| [Cloudflare speedtest](https://github.com/cloudflare/speedtest) | 1.14.1 | Maintained browser HTTP measurement engine; no packet loss or scores enabled | MIT; retain copyright/license notice |
| [jsPDF](https://github.com/parallax/jsPDF) | 4.2.1 | Client PDF text/vector document generation | MIT; retain notice |
| [jsPDF AutoTable](https://github.com/simonbengtsson/jsPDF-AutoTable) | 5.0.8 | Semantic tables and pagination, compatible with jsPDF 4 | MIT; retain notice |
| Next.js / eslint-config-next | 16.3.8 | Compatible security patch to existing framework/tooling | Existing MIT dependency; lockfile retained |

Versions are exact in package.json and transitive versions/integrity hashes are
locked in package-lock.json. `npm ci` is the reproducible install. Runtime uses
Node >=22, with 24.19.0 observed here. No copied privileged script is introduced
by these frontend dependencies. These are focused additions to the current app.

`frontend/public/THIRD_PARTY_NOTICES.txt` preserves full installed license notices
for the new libraries and installed production/optional PDF dependencies: Babel
runtime, fflate, fast-png, iobuffer, pako, canvg, core-js, DOMPurify, html2canvas,
raf, rgbcolor, stackblur-canvas, svg-pathdata, text-segmentation, utrie,
base64-arraybuffer and performance-now. Some are optional bundled capabilities
not used by NetSentinel. No dashboard screenshot/HTML-rendering code is invoked.
Keep bundled notices and this file when redistributing; regenerating a lockfile
requires reviewing new dependencies and updating their notices.

## Maintenance and security review

Registry metadata, upstream documentation/licenses and security pages were
reviewed. Cloudflare's 1.14.1 TypeScript API supports real phase callbacks and
abort on pause. jsPDF/AutoTable 4.2.1/5.0.8 are compatible current published
versions. The application does not invoke jsPDF's HTML, annotation, AcroForm,
image loading or addJS features, reducing exposure to historical vulnerable APIs.
Upstream advisories remain worth monitoring:

- <https://github.com/parallax/jsPDF/security/advisories>
- <https://github.com/cloudflare/speedtest/security>
- <https://github.com/advisories/GHSA-vcvr-r3jv-pc5j>

Initial audit identified the existing Next 16.3.5 critical ImageResponse advisory
and high-severity brace-expansion issues in lint dependencies. Next and matching
eslint config were patched to 16.3.8; compatible brace-expansion transitive
updates were applied. The completed install audit reported **0 vulnerabilities**.
This is the advisory database result at review time, not a security guarantee.
Run a fresh `npm audit` for each release. No force-major audit repair was used.

## Service selection is separate from source licensing

Cloudflare provides the measurement endpoints documented by its open-source
engine. Public endpoint service policies, CORS, rate limits and bandwidth costs
are not granted by the MIT code license. NetSentinel discloses external requests,
bounds test payload attempts/duration and disables engine result logging. No SLA
or permanent free endpoint availability is promised.

IPWHOIS/ipwho.is is a hosted provider, not bundled source code. Its current free
tier documents CORS, 1,000 lookups/day shared per domain and commercial use.
Only the requesting browser's own public details are shown, after consent.
No provider database, general IP query tool, API key or paid subscription is
redistributed. Respect their current terms and handle 429/unavailability.

See [measurement/service review](PUBLIC_MEASUREMENTS.md) for official policy
links, numerical limits, calculations, rejected alternatives and outstanding
live-service verification.
