import { test, expect } from "@playwright/test";
import { createServer } from "node:http";

// An isolated loopback upstream, not Django or stored LIVE telemetry.
const upstream = createServer((req, res) => {
  if (req.url !== "/api/v1/health/" || req.method !== "GET" || req.headers.origin || req.headers.cookie) {
    res.writeHead(400).end(); return;
  }
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ status: "ok", database: "reachable" }));
});
test.beforeAll(async () => { await new Promise<void>((resolve, reject) => { upstream.once("error", reject); upstream.listen(3103, "127.0.0.1", resolve); }); });
test.afterAll(async () => { await new Promise<void>((resolve, reject) => upstream.close((error) => error ? reject(error) : resolve())); });

// Deliberately do not intercept /api/backend: exercise the real Next route boundary.
test("real browser GET without Origin reaches the server route allowlist", async ({ page }) => {
  await page.goto("/local");
  const requestPromise = page.waitForRequest("**/api/backend/not-allowed");
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/backend/not-allowed");
    return { status: response.status, body: await response.json() };
  });
  const request = await requestPromise;
  expect(await request.headerValue("origin")).toBeNull();
  expect(await request.headerValue("sec-fetch-site")).toBe("same-origin");
  expect(result).toEqual({ status: 404, body: { error: "Unknown resource." } });
  const health = await page.evaluate(async () => {
    const response = await fetch("/api/backend/health");
    return { status: response.status, body: await response.json() };
  });
  expect(health).toEqual({ status: 200, body: { status: "ok", database: "reachable" } });
});

test("real server accepts local CLI reads but rejects hostile origins and mutations", async ({ request }) => {
  const local = await request.get("/api/backend/not-allowed");
  expect(local.status()).toBe(404);
  const hostile = await request.get("/api/backend/health", { headers: { origin: "https://example.com" } });
  expect(hostile.status()).toBe(403);
  const post = await request.post("/api/backend/health");
  expect(post.status()).toBe(405);
});
