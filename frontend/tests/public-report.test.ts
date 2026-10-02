import { test } from "node:test";
import assert from "node:assert/strict";
import { createPublicPdf, publicReportModel, type PublicReportOptions } from "../src/lib/public-report";
import type { SpeedResult } from "../src/lib/public-measurements";

export function reportFixture(): PublicReportOptions {
  const speeds: SpeedResult[] = Array.from({ length: 30 }, (_, i) => ({ id: crypto.randomUUID(), at: `2026-09-${String(i + 1).padStart(2, "0")}T12:00:00.000Z`, version: 1, scope: "LIVE", source: "Cloudflare edge", status: "complete", downloadMbps: 12 + i, uploadMbps: 4 + i / 10, latencyMs: 24, jitterMs: 3, latencySamples: [20, 23, 26, 23, 26, 23], receivedBodyBytes: 11_000_000, confirmedUploadBytes: 4_500_000, accountingIncomplete: false, durationMs: 12500 }));
  return { checks: [], speeds, network: { at: "2026-09-25T12:00:00.000Z", source: "ipwho.is", ip: "192.0.2.40", family: "IPv4", organization: "NON-PRIVATE EXAMPLE NETWORK WITH A LONG ORGANIZATION NAME FOR TABLE WRAPPING ".repeat(2), asn: "AS64500", city: "Example City", region: "Example Region", country: "Example Country" }, from: "2026-09-01", to: "2026-09-30", includeChecks: true, includeSpeeds: true, includeNetwork: true, includeIp: false, includeLocation: false, generatedAt: "2026-10-02T00:00:00.000Z", example: true };
}
test("report hides IP and location by default, excludes unavailable sections and respects UTC dates", () => {
  const options = reportFixture(), model = publicReportModel(options);
  assert.equal(model.network?.ip, "Hidden by default"); assert.equal(model.network?.location, "Hidden by default"); assert.ok(!JSON.stringify(model).includes("192.0.2.40"));
  assert.equal(publicReportModel({ ...options, from: "2026-09-25", to: "2026-09-25" }).speeds.length, 1);
  assert.equal(publicReportModel({ ...options, includeSpeeds: false }).speeds.length, 0);
  assert.equal(publicReportModel({ ...options, from: "2026-09-26" }).network, null);
  assert.throws(() => publicReportModel({ ...options, from: "2026-10-01" }), /start date/);
  const unredacted = publicReportModel({ ...options, includeIp: true, includeLocation: true }); assert.equal(unredacted.network?.ip, "192.0.2.40"); assert.match(unredacted.network?.location ?? "", /Example City/);
});
test("real PDF has semantic text, multiple pages, provenance and no default private values", () => {
  const pdf = createPublicPdf(reportFixture()); const text = pdf.output();
  assert.ok(pdf.getNumberOfPages() >= 3); assert.match(text, /^%PDF-/); assert.match(text, /NetSentinel/); assert.match(text, /SIMULATION/); assert.match(text, /Hidden by default/); assert.match(text, /Unavailable|available/); assert.doesNotMatch(text, /192\.0\.2\.40|Example City|Example Region/);
  assert.match(text, /Download comparison/); assert.match(text, /Completed payloads/);
});
