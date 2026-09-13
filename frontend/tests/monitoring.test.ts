import { test } from "node:test";
import assert from "node:assert/strict";
import { decodePage, decodeSession, statusFreshness, type CaptureStatus } from "../src/lib/contracts";
import { upstreamURL } from "../src/lib/gateway";
const selection = { session: "11111111-1111-1111-1111-111111111111", mode: "SIMULATION" as const };
const session = { session_id: selection.session, mode: selection.mode, run_id: "33333333-3333-3333-3333-333333333333",
  source_id: "44444444-4444-4444-4444-444444444444", interface_name: "fixture", started_at: "2026-09-13T00:00:00Z",
  received_at: "2026-09-13T00:00:01Z", observation_profile: "fixture-profile", schema_version: "backend-v1" };
const status = { ...session, id: "22222222-2222-2222-2222-222222222222", observed_at: "2026-09-13T00:01:00Z",
  state: "RECOVERING" as const, valid: false, reason: "fixture_gap", loss_started_at: "2026-09-13T00:00:50Z",
  gap_ended_at: null, monitoring_gap_seconds: 10, recovery_attempts: 2 };
test("session decoder preserves full metadata and rejects mismatched identities", () => {
  assert.deepEqual(decodeSession(session, selection), session);
  for (const changes of [{ session_id: session.source_id }, { mode: "LIVE" }, { started_at: "invalid" }, { source_id: "bad" }])
    assert.throws(() => decodeSession({ ...session, ...changes }, selection));
});
test("capture decoder retains recorded gap, validity and recovery fields", () => {
  const row = decodePage<CaptureStatus>({ next: null, results: [status] }, "capture-status", selection).results[0];
  assert.equal(row.state, "RECOVERING"); assert.equal(row.monitoring_gap_seconds, 10);
  assert.equal(row.recovery_attempts, 2); assert.equal(row.gap_ended_at, null); assert.equal(row.valid, false);
});
test("capture decoder rejects missing, unsafe, cross-mode and inconsistent values", () => {
  for (const changes of [{ mode: "LIVE" }, { session_id: session.source_id }, { state: "RUNNING" },
    { monitoring_gap_seconds: null }, { monitoring_gap_seconds: -1 }, { recovery_attempts: 2 ** 53 }, { observed_at: "yesterday" }])
    assert.throws(() => decodePage({ next: null, results: [{ ...status, ...changes }] }, "capture-status", selection));
});
test("stale status remains historical and does not assert current capture health", () => {
  const now = Date.parse(status.observed_at);
  assert.match(statusFreshness(status, now), /Recent report/);
  assert.match(statusFreshness(status, now + 15001), /Stale report.*unavailable/);
  assert.match(statusFreshness(status, now - 1), /Future observation/);
});
test("new read routes require scope; only capture list has a bounded limit", () => {
  const query = new URLSearchParams({ session_id: selection.session, mode: selection.mode });
  for (const resource of ["capture-status", "monitoring-sessions"]) {
    const url = upstreamURL("http://127.0.0.1:8001/api/v1/", resource, query);
    assert.equal(url.pathname, `/api/v1/${resource}/`);
    assert.equal(url.searchParams.get("session_id"), selection.session);
    assert.equal(url.searchParams.get("limit"), resource === "capture-status" ? "20" : null);
    assert.throws(() => upstreamURL("http://127.0.0.1:8001/api/v1/", resource, new URLSearchParams()));
  }
});
