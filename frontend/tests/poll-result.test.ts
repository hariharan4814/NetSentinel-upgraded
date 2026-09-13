import { test } from "node:test";
import assert from "node:assert/strict";
import { retainOnError } from "../src/lib/poll-result";
import { currentRate, type Sample } from "../src/lib/contracts";

test("failed refresh preserves previous data alongside the error", () => {
  const data = { results: [{ observed_at: "2026-09-13T00:00:00Z" }] };
  const result = retainOnError({ data }, { error: "offline" });
  assert.equal(result.data, data);
  assert.equal(result.error, "offline");
  assert.equal(retainOnError(result, { error: "still offline" }).data, data);
});
test("failure before first load does not invent historical data", () => {
  assert.equal(retainOnError({}, { error: "offline" }).data, undefined);
});
test("successful empty or updated responses replace old data and clear errors", () => {
  const previous = { data: { results: [1] }, error: "offline" };
  assert.deepEqual(retainOnError(previous, { data: { results: [] } }), { data: { results: [] } });
  assert.deepEqual(retainOnError(previous, { data: { results: [2] } }), { data: { results: [2] } });
});
test("retaining or re-fetching a sample never refreshes its observation time", () => {
  const sample = { observed_at: "2026-09-13T00:00:00Z", valid: true, upload_bytes_per_second: 1024 } as Sample;
  const result = retainOnError({ data: sample }, { error: "offline" });
  const observed = Date.parse(sample.observed_at);
  assert.equal(currentRate(result.data, "upload", observed + 1000, false), null);
  const recovered = retainOnError(result, { data: sample });
  assert.equal(currentRate(recovered.data, "upload", observed + 6000, true), null);
  assert.equal(recovered.data?.observed_at, sample.observed_at);
});
