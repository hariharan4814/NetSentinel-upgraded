import { test } from "node:test";
import assert from "node:assert/strict";
import { currentRate, decodePage, formatRate, pollDelay, type Sample } from "../src/lib/contracts";
import { localRequest, upstreamURL } from "../src/lib/gateway";

const selection = { session: "11111111-1111-1111-1111-111111111111", mode: "SIMULATION" as const };
const now = Date.parse("2026-09-13T10:00:00Z");
const sample: Sample = {
  id: "22222222-2222-2222-2222-222222222222", session_id: selection.session,
  run_id: "33333333-3333-3333-3333-333333333333", interface_name: "fixture", mode: "SIMULATION",
  observed_at: "2026-09-13T10:00:00Z", valid: true, reason: null,
  upload_bytes_per_second: 1024, download_bytes_per_second: 0, packets_sent: 10, packets_received: 0,
};
test("valid zero rate remains distinct from missing data", () => {
  assert.equal(currentRate(sample, "download", now, true), 0);
  assert.equal(formatRate(null), "Unavailable");
  assert.equal(formatRate(0), "0.0 B/s");
});
test("invalid, stale, future and offline observations cannot appear current", () => {
  for (const [row, time, available] of [
    [{ ...sample, valid: false }, now, true], [sample, now + 5001, true],
    [sample, now - 1, true], [sample, now, false], [undefined, now, true],
  ] as const) assert.equal(currentRate(row, "upload", time, available), null);
});
test("decoder preserves invalid null measurements and explicit reason", () => {
  const invalid = { ...sample, valid: false, reason: "counter_gap", upload_bytes_per_second: null, download_bytes_per_second: null };
  assert.equal(decodePage<Sample>({ next: null, results: [invalid] }, "telemetry", selection).results[0].upload_bytes_per_second, null);
});
test("decoder rejects cross-mode and cross-session responses", () => {
  for (const changed of [{ mode: "LIVE" }, { session_id: "44444444-4444-4444-4444-444444444444" }])
    assert.throws(() => decodePage({ next: null, results: [{ ...sample, ...changed }] }, "telemetry", selection), /provenance/);
});
test("decoder rejects malformed timestamps, unsafe counts and missing rates", () => {
  for (const changed of [{ observed_at: "2026-09-13T10:00:00" }, { packets_sent: 2 ** 53 }, { upload_bytes_per_second: null }, { download_bytes_per_second: -1 }])
    assert.throws(() => decodePage({ next: null, results: [{ ...sample, ...changed }] }, "telemetry", selection));
});
test("empty API page is valid; unbounded pages are rejected", () => {
  assert.deepEqual(decodePage({ next: null, results: [] }, "telemetry", selection).results, []);
  assert.throws(() => decodePage({ next: null, results: Array(61).fill(sample) }, "telemetry", selection));
});
test("read gateway allows only fixed local API paths and bounded queries", () => {
  const query = new URLSearchParams({ session_id: selection.session, mode: selection.mode, limit: "99999", url: "http://example.com" });
  const url = upstreamURL("http://127.0.0.1:8001/api/v1/", "telemetry", query);
  assert.equal(url.pathname, "/api/v1/telemetry/");
  assert.equal(url.searchParams.get("limit"), "60");
  assert.equal(url.searchParams.has("url"), false);
  assert.throws(() => upstreamURL(url.origin + "/api/v1/", "alerts", query));
  assert.throws(() => upstreamURL(url.origin + "/api/v1/", "telemetry", new URLSearchParams()));
});
test("gateway rejects missing, credential-bearing and non-local configuration", () => {
  for (const base of [undefined, "http://example.com/api/v1/", "http://user:secret@localhost/api/v1/", "file:///api/v1/", "http://localhost/other/"])
    assert.throws(() => upstreamURL(base, "health", new URLSearchParams()));
});
test("browser boundary rejects cross-origin, cross-site and DNS-rebinding hosts", () => {
  const req = (headers: Record<string,string>, url = "http://127.0.0.1:3000/api/backend/health") => new Request(url, { headers });
  assert.equal(localRequest(req({ host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000" })), true);
  assert.equal(localRequest(req({ host: "127.0.0.1:3000", origin: "https://example.com" })), false);
  assert.equal(localRequest(req({ host: "127.0.0.1:3000", "sec-fetch-site": "cross-site" })), false);
  assert.equal(localRequest(req({ host: "example.com" })), false);
});
test("poll backoff grows and is capped", () => {
  assert.deepEqual([0,1,2,3,4,100].map(pollDelay), [2000,4000,8000,16000,30000,30000]);
});
