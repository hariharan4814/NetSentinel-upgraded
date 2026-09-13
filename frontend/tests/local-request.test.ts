import { test } from "node:test";
import assert from "node:assert/strict";
import { NextRequest } from "next/server";
import { localRequest } from "../src/lib/gateway";

const browser = (host = "127.0.0.1:3000", extra: Record<string, string> = {}) =>
  new NextRequest(`http://${host}/api/backend/health`, { headers: { host, "sec-fetch-site": "same-origin", ...extra } });

test("actual NextRequest loopback normalization permits genuine browser origin", () => {
  const request = browser("127.0.0.1:3000", { origin: "http://127.0.0.1:3000" });
  assert.equal(new URL(request.url).hostname, "localhost");
  assert.equal(request.headers.get("host"), "127.0.0.1:3000");
  assert.equal(localRequest(request), true);
});
test("same-origin GET may omit both Origin and Referer", () => {
  assert.equal(browser().headers.get("origin"), null);
  assert.equal(localRequest(browser()), true);
  assert.equal(localRequest(browser("127.0.0.1:3000", { referer: "http://127.0.0.1:3000/" })), true);
});
test("localhost and IPv6 are supported individually, not interchangeable origins", () => {
  for (const host of ["localhost:3000", "[::1]:3000"])
    assert.equal(localRequest(browser(host, { origin: `http://${host}` })), true);
  assert.equal(localRequest(browser("127.0.0.1:3000", { origin: "http://localhost:3000" })), false);
});
test("cross-origin, non-local and opaque sources are rejected", () => {
  for (const origin of ["http://127.0.0.1:4000", "https://127.0.0.1:3000", "https://example.com", "null", ""])
    assert.equal(localRequest(browser("127.0.0.1:3000", { origin })), false);
  for (const referer of ["http://localhost:3000/", "https://example.com/", "invalid"])
    assert.equal(localRequest(browser("127.0.0.1:3000", { referer })), false);
  for (const site of ["cross-site", "same-site", "invalid"])
    assert.equal(localRequest(browser("127.0.0.1:3000", { "sec-fetch-site": site })), false);
});
test("malformed, non-local and mismatched Host authorities fail closed", () => {
  for (const host of ["example.com:3000", "localhost:4000", "localhost:99999", "localhost:3000/path",
    "user@localhost:3000", "127.1:3000", "localhost:3000,example.com", "", "localhost:03000"])
    assert.equal(localRequest(browser("127.0.0.1:3000", { host })), false);
  assert.equal(localRequest(new Request("http://example.com:3000/api/backend/health", { headers: { host: "localhost:3000" } })), false);
});
test("forwarded headers cannot override Host or rescue a hostile origin", () => {
  const forwarded = { "x-forwarded-host": "example.com", "x-forwarded-proto": "https", forwarded: "host=example.com;proto=https" };
  assert.equal(localRequest(browser("127.0.0.1:3000", forwarded)), true);
  assert.equal(localRequest(browser("127.0.0.1:3000", { ...forwarded, origin: "https://example.com" })), false);
  assert.equal(localRequest(browser("127.0.0.1:3000", { host: "example.com", "x-forwarded-host": "127.0.0.1:3000" })), false);
});
