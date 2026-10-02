import { test } from "node:test";
import assert from "node:assert/strict";
import { lookupNetwork, meanJitter, median, parseNetworkDetails, parseSpeedHistory, payloadMbps, runSpeedTest, speedConfig, summarizeSpeed, SPEED_HISTORY_AGE, type SpeedEngine, type SpeedResult } from "../src/lib/public-measurements";

function results() {
  return { getUnloadedLatencyPoints: () => [20, 40, 30],
    getDownloadBandwidthPoints: () => [{ bytes: 1_000_000, duration: 800, bps: 10_050_000, ping: 20, measTime: new Date(), serverTime: 5, transferSize: 1_005_000 }],
    getUploadBandwidthPoints: () => [{ bytes: 500_000, duration: 1000, bps: 4_020_000, ping: 20, measTime: new Date(), serverTime: 5, transferSize: 200 }],
  };
}
const resources = () => [{ name: "https://speed.cloudflare.com/__down?bytes=1000000", decodedBodySize: 1_000_000, responseEnd: 800 }];
const fixture = (): SpeedResult => summarizeSpeed(results(), resources(), "complete", 2000);
test("speed math uses measured payload units, median and adjacent differences, never wire estimates", () => {
  assert.equal(payloadMbps([{ bytes: 1_000_000, duration: 800 }]), 10);
  assert.equal(payloadMbps([{ bytes: 1_000_000, duration: 1 }]), null);
  assert.equal(meanJitter([20, 40, 30]), 15); assert.equal(meanJitter([20]), null); assert.equal(median([40, 20, 30]), 30);
  const summary = fixture(); assert.equal(summary.downloadMbps, 10); assert.equal(summary.uploadMbps, 4); assert.equal(summary.receivedBodyBytes, 1_000_000); assert.equal(summary.confirmedUploadBytes, 500_000);
  assert.equal(summary.accountingIncomplete, false);
});
test("missing or mismatched body observations cannot become measured throughput or zero bytes", () => {
  const missing = summarizeSpeed(results(), [], "failed", 500);
  assert.equal(missing.downloadMbps, null); assert.equal(missing.receivedBodyBytes, null); assert.equal(missing.accountingIncomplete, true);
  const mismatch = summarizeSpeed(results(), [{ ...resources()[0], decodedBodySize: 300 }], "complete", 500);
  assert.equal(mismatch.downloadMbps, null); assert.equal(mismatch.receivedBodyBytes, 300); assert.equal(mismatch.accountingIncomplete, true);
});
function mockEngine(action: (e: SpeedEngine) => void) {
  let pauses = 0;
  const engine: SpeedEngine = { results: results(), onPhaseChange: () => {}, onResultsChange: () => {}, onFinish: () => {}, onError: () => {}, pause: () => { pauses++; }, play: () => action(engine) };
  return { engine, pauses: () => pauses };
}
test("cancellation stops the engine and labels partial accounting without a completed history record", async () => {
  const controller = new AbortController(); const fake = mockEngine(() => controller.abort());
  const measured = await runSpeedTest({ signal: controller.signal, engineFactory: async () => fake.engine, resources, onProgress: () => {} });
  assert.equal(measured.status, "cancelled"); assert.equal(measured.accountingIncomplete, true); assert.equal(fake.pauses(), 1); assert.equal(parseSpeedHistory(JSON.stringify([measured])).length, 0);
});
test("deadline and endpoint errors settle with explicit failures; no scores or telemetry are configured", async () => {
  const fake = mockEngine(() => {});
  const result = await runSpeedTest({ signal: new AbortController().signal, engineFactory: async () => fake.engine, resources, onProgress: () => {}, timeoutMs: 5 });
  assert.equal(result.status, "timed-out"); assert.equal(fake.pauses(), 1);
  const error = mockEngine(e => e.onError("endpoint unavailable"));
  assert.equal((await runSpeedTest({ signal: new AbortController().signal, engineFactory: async () => error.engine, resources, onProgress: () => {} })).status, "failed");
  assert.equal(speedConfig.logAimApiUrl, null); assert.equal(speedConfig.logMeasurementApiUrl, null); assert.equal(speedConfig.autoStart, false);
  assert.ok(speedConfig.measurements?.every(m => m.type !== "packetLoss"));
});
test("history is bounded, expiry-aware, rejects malformed values, strips personal fields and deduplicates", () => {
  const item = fixture(); const raw = [{ ...item, ip: "192.0.2.1", location: "fixture" }, item, { ...item, id: "bad" }, { ...item, at: new Date(Date.now() - SPEED_HISTORY_AGE - 1).toISOString() }, { ...item, downloadMbps: -1 }];
  const parsed = parseSpeedHistory(JSON.stringify(raw)); assert.equal(parsed.length, 1); assert.equal("ip" in parsed[0], false); assert.equal("location" in parsed[0], false);
  assert.deepEqual(parseSpeedHistory("broken"), []); assert.deepEqual(parseSpeedHistory("x".repeat(100001)), []);
  assert.equal(parseSpeedHistory(JSON.stringify(Array.from({ length: 40 }, () => ({ ...item, id: crypto.randomUUID() })))).length, 30);
});
test("lookup handles missing optional fields and retains only allowed provider fields", () => {
  const parsed = parseNetworkDetails({ success: true, ip: "2001:db8::1", secret: "discard", connection: { asn: 64500, org: "Example\nCompany" }, city: null });
  assert.equal(parsed.family, "IPv6"); assert.equal(parsed.organization, "ExampleCompany"); assert.equal(parsed.asn, "AS64500"); assert.equal(parsed.city, null); assert.equal("secret" in parsed, false);
  assert.throws(() => parseNetworkDetails({ success: false })); assert.throws(() => parseNetworkDetails({ success: true, ip: "999.0.0.1" }));
});
test("lookup is a single direct credentialless request, handles rate limits and caps response size", async () => {
  let calls = 0;
  const fetched = await lookupNetwork(new AbortController().signal, async (url, options) => { calls++; assert.equal(String(url), "https://ipwho.is/?fields=success,ip,type,city,region,country,connection"); assert.equal(options?.credentials, "omit"); assert.equal(options?.redirect, "error"); return Response.json({ success: true, ip: "192.0.2.10" }); });
  assert.equal(fetched.family, "IPv4"); assert.equal(calls, 1);
  await assert.rejects(lookupNetwork(new AbortController().signal, async () => new Response(null, { status: 429 })), /daily limit/);
  await assert.rejects(lookupNetwork(new AbortController().signal, async () => new Response("x".repeat(17000), { headers: { "content-type": "application/json" } })), /too large/);
});
