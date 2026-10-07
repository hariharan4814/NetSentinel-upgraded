import { test } from "node:test";
import assert from "node:assert/strict";
import { GET } from "../src/app/api/backend/[resource]/route";
import { NextRequest } from "next/server";
import { login, SESSION_COOKIE } from "../src/lib/local-auth";

process.env.NETSENTINEL_OPERATOR_PASSWORD = "fixture-operator-password-not-for-runtime";
process.env.NETSENTINEL_READ_TOKEN = "fixture-read-only-token-not-for-runtime";
const session = login(process.env.NETSENTINEL_OPERATOR_PASSWORD).token!;

const request = (path = "health", origin = "http://127.0.0.1:3000") => new Request(`http://127.0.0.1:3000/api/backend/${path}`, { headers: { host: "127.0.0.1:3000", origin, cookie: `${SESSION_COOKIE}=${session}` } });
const context = (resource: string) => ({ params: Promise.resolve({ resource }) });

test("gateway returns errors without forwarding cross-origin or unapproved resources", async () => {
  assert.equal((await GET(request("health", "https://example.com"), context("health"))).status, 403);
  assert.equal((await GET(request("alerts"), context("alerts"))).status, 404);
  assert.equal((await GET(new NextRequest("http://127.0.0.1:3000/api/backend/alerts", {
    headers: { host: "127.0.0.1:3000", "sec-fetch-site": "same-origin" },
  }), context("alerts"))).status, 404);
});
test("gateway strips browser credentials, uses GET and prevents caching", async (t) => {
  t.mock.method(globalThis, "fetch", async (_url: unknown, options: RequestInit) => {
    assert.equal(options.method, undefined); // fetch defaults to GET
    assert.deepEqual(options.headers, { Accept: "application/json", Authorization: `Bearer ${process.env.NETSENTINEL_READ_TOKEN}` });
    assert.equal(options.cache, "no-store"); assert.equal(options.redirect, "error");
    return Response.json({ status: "ok", database: "reachable" });
  });
  const previous = process.env.BACKEND_API_BASE_URL;
  process.env.BACKEND_API_BASE_URL = "http://127.0.0.1:8001/api/v1/";
  try {
    const result = await GET(request(), context("health"));
    assert.equal(result.status, 200); assert.equal(result.headers.get("cache-control"), "no-store");
  } finally { if (previous === undefined) delete process.env.BACKEND_API_BASE_URL; else process.env.BACKEND_API_BASE_URL = previous; }
});
test("gateway rejects unauthenticated reads without contacting upstream", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { assert.fail("unauthenticated upstream request"); });
  const response = await GET(new Request("http://127.0.0.1:3000/api/backend/health", { headers: { host: "127.0.0.1:3000" } }), context("health"));
  assert.equal(response.status, 401);
  assert.equal(response.headers.get("cache-control"), "no-store");
});
test("gateway redacts network failure details", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { throw new Error("private network detail"); });
  const previous = process.env.BACKEND_API_BASE_URL;
  process.env.BACKEND_API_BASE_URL = "http://127.0.0.1:8001/api/v1/";
  try {
    const result = await GET(request(), context("health"));
    assert.equal(result.status, 503); assert.doesNotMatch(await result.text(), /private/);
  } finally { if (previous === undefined) delete process.env.BACKEND_API_BASE_URL; else process.env.BACKEND_API_BASE_URL = previous; }
});
