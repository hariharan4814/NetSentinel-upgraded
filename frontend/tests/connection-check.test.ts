import { test } from "node:test";
import assert from "node:assert/strict";
import { CHECK_VERSION, MAX_AGE_MS, interpretation, measurementScope, parseHistory, runCheck, summarize, supportReport, transferSeconds, type Check } from "../src/lib/connection-check";

const fixture = (scope: "LIVE" | "LOCAL" = "LIVE"): Check => ({ id: "11111111-1111-4111-8111-111111111111", at: new Date().toISOString(), version: CHECK_VERSION, scope, probes: [20, 30, 40, 50, 60, 70, 80, 90].map(ms => ({ ms })) });

test("summary uses successful measurements only and does not turn missing data into zero", () => {
  assert.deepEqual(summarize([{ ms: 10 }, { ms: null }, { ms: 30 }]), { median: 20, spread: 20, success: 2, failed: 1, total: 3 });
  assert.deepEqual(summarize([{ ms: null }]), { median: null, spread: null, success: 0, failed: 1, total: 1 });
  assert.equal(summarize([{ ms: 10 }]).spread, null);
});
test("local/IP measurements never make an internet quality claim", () => {
  for (const host of ["localhost", "127.0.0.1", "[::1]", "192.168.1.10", "test.local", "10.0.0.1"]) assert.equal(measurementScope(host), "LOCAL");
  assert.equal(measurementScope("netsentinel.example.com"), "LIVE");
  assert.equal(interpretation(fixture("LOCAL")).title, "Local check complete");
});
test("advisory thresholds include the boundary and failures take priority", () => {
  const check = fixture();
  assert.equal(interpretation(check).tone, "good");
  check.probes = Array.from({ length: 8 }, () => ({ ms: 300 }));
  assert.equal(interpretation(check).tone, "warning");
  check.probes[0].ms = null;
  assert.equal(interpretation(check).title, "Some requests didn’t complete");
  check.probes = check.probes.map(() => ({ ms: null }));
  assert.equal(interpretation(check).title, "This site didn’t respond");
});
test("check bounds requests, validates fixed endpoint response, and preserves failures", async () => {
  let calls = 0;
  const result = await runCheck({ signal: new AbortController().signal, pauseMs: 0, onProgress: () => {}, fetcher: async (input, options) => {
    assert.match(String(input), /^\/connection-check\.json\?check=/);
    assert.equal(options?.cache, "no-store"); assert.equal(options?.credentials, "omit");
    assert.equal(options?.redirect, "error");
    calls++;
    if (calls === 1) return new Response("portal", { headers: { "content-type": "text/html" } });
    if (calls === 2) return Response.json({ service: "other", version: 1 });
    if (calls === 3) return new Response(null, { status: 503 });
    return Response.json({ service: "netsentinel-connectivity", version: 1 });
  } });
  assert.equal(calls, 8); assert.equal(summarize(result).success, 5);
  assert.deepEqual(result.slice(0, 3), [{ ms: null }, { ms: null }, { ms: null }]);
});
test("cancellation stops future probes instead of returning a completed partial check", async () => {
  const controller = new AbortController(); let calls = 0;
  await assert.rejects(runCheck({ signal: controller.signal, pauseMs: 0,
    onProgress: () => controller.abort(), fetcher: async () => { calls++; return Response.json({ service: "netsentinel-connectivity", version: 1 }); },
  }));
  assert.equal(calls, 1);
});
test("history drops invalid, expired, future, partial and duplicate records, and unknown fields", () => {
  const check = fixture(); const now = Date.now();
  const dirty = [check, check, { ...check, id: "x" }, { ...check, at: new Date(now - MAX_AGE_MS - 1).toISOString() },
    { ...check, at: new Date(now + 50000).toISOString() }, { ...check, probes: [{ ms: 20 }] }, { ...check, scope: "SIMULATION" }];
  assert.equal(parseHistory(JSON.stringify(dirty), now).length, 1);
  assert.deepEqual(parseHistory("bad json"), []);
  assert.deepEqual(parseHistory(JSON.stringify([{ ...check, probes: Array(8).fill({ ms: -1 }) }])), []);
  assert.equal("secret" in parseHistory(JSON.stringify([{ ...check, secret: "discard" }]))[0], false);
});
test("history remains bounded and reports retain measurement source and limitations", () => {
  const checks = Array.from({ length: 12 }, (_, i) => ({ ...fixture(), id: `11111111-1111-4111-8111-${String(i).padStart(12, "0")}` }));
  assert.equal(parseHistory(JSON.stringify(checks)).length, 10);
  assert.match(supportReport(fixture("LOCAL")), /Source: LOCAL/);
  assert.match(supportReport(fixture()), /not measure download\/upload speed/);
});
test("transfer calculation uses bits/bytes and rejects invalid inputs", () => {
  assert.equal(transferSeconds(1, "GB", 50), 160);
  assert.equal(transferSeconds(25, "MB", 10), 20);
  for (const value of [0, -1, Infinity, NaN, 100001]) assert.equal(transferSeconds(1, "GB", value), null);
});
