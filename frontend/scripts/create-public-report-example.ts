// Explicit non-private QA fixture. Never loaded by the application or public build.
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createPublicPdf } from "../src/lib/public-report";
import type { SpeedResult } from "../src/lib/public-measurements";

const speeds: SpeedResult[] = Array.from({ length: 30 }, (_, i) => ({ id: crypto.randomUUID(), at: `2026-09-${String(i + 1).padStart(2, "0")}T12:00:00.000Z`, version: 1, scope: "LIVE", source: "Cloudflare edge", status: "complete", downloadMbps: 12 + i, uploadMbps: 4 + i / 10, latencyMs: 24, jitterMs: 3, latencySamples: [20, 23, 26, 23, 26, 23], receivedBodyBytes: 11_000_000, confirmedUploadBytes: 4_500_000, accountingIncomplete: false, durationMs: 12500 }));
async function main() {
  const pdf = createPublicPdf({ checks: [], speeds, network: { at: "2026-09-25T12:00:00.000Z", source: "ipwho.is", ip: "192.0.2.40", family: "IPv4", organization: "NON-PRIVATE EXAMPLE NETWORK WITH A LONG ORGANIZATION NAME FOR TABLE WRAPPING ".repeat(2), asn: "AS64500", city: "Example City", region: "Example Region", country: "Example Country" }, from: "2026-09-01", to: "2026-09-30", includeChecks: true, includeSpeeds: true, includeNetwork: true, includeIp: false, includeLocation: false, generatedAt: "2026-10-02T00:00:00.000Z", example: true });
  const directory = path.resolve(process.cwd(), "../docs/examples");
  await mkdir(directory, { recursive: true });
  await writeFile(path.join(directory, "public-report-simulation.pdf"), new Uint8Array(pdf.output("arraybuffer")));
  console.log(`Created labelled SIMULATION report with ${pdf.getNumberOfPages()} pages.`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
