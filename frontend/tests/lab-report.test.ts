import { test } from "node:test";
import assert from "node:assert/strict";
import { createLabPdf, labReportModel } from "../src/lib/lab-report";
import { labFixture } from "./fixtures/lab-result";
test("lab report refuses LIVE and excludes arbitrary top-level secret metadata", () => {
  const fixture = labFixture();
  assert.throws(() => labReportModel({ ...fixture, mode: "LIVE" } as never));
  const model = labReportModel({ ...fixture, credentials: "private-secret-sentinel" } as never);
  assert.doesNotMatch(JSON.stringify(model), /private-secret-sentinel/);
});
test("lab PDF has semantic evidence, unavailable values, wrapped long content and numbered pages", () => {
  const fixture = labFixture();
  fixture.performance.inference_p95_ms = null;
  fixture.limitations.push("Long labelled fixture limitation for wrapping and pagination. ".repeat(80));
  const pdf = createLabPdf(fixture);
  const bytes = pdf.output();
  assert.match(bytes, /^%PDF-/); assert.ok(pdf.getNumberOfPages() >= 3);
  for (const label of ["SIMULATION", "Computed model comparison", "Isolation Forest deviation", "Selected explanation evidence", "Unavailable", "Limits and privacy", "not attack probabilities"]) assert.ok(bytes.includes(label), label);
  assert.match(bytes, /1 \/ \d+/);
});
