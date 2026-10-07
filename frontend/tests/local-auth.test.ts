import { test } from "node:test";
import assert from "node:assert/strict";
import { GET, POST, DELETE } from "../src/app/api/local-auth/route";
import { login, localSession, SESSION_COOKIE, SESSION_SECONDS } from "../src/lib/local-auth";

const password = "fixture-operator-password-not-for-runtime";
process.env.NETSENTINEL_OPERATOR_PASSWORD = password;
process.env.NETSENTINEL_READ_TOKEN = "fixture-read-only-token-not-for-runtime";
const req = (method = "GET", extra: Record<string, string> = {}, body?: string) => new Request("http://127.0.0.1:3000/api/local-auth", {
  method, headers: { host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000", "x-netsentinel-request": "local-ui-v1", "content-type": "application/json", ...extra }, ...(body === undefined ? {} : { body }),
});

test("local login issues protected cookie and logout revokes copied tokens", async () => {
  const response = await POST(req("POST", {}, JSON.stringify({ password })));
  assert.equal(response.status, 200);
  const cookie = response.headers.get("set-cookie")!;
  assert.match(cookie, /HttpOnly; SameSite=Strict; Max-Age=14400/);
  assert.doesNotMatch(await response.clone().text(), new RegExp(password));
  const sessionCookie = cookie.split(";")[0];
  const authenticated = await GET(req("GET", { cookie: sessionCookie }));
  assert.equal(authenticated.status, 200);
  const csrf = (await authenticated.json()).csrf;
  assert.equal((await DELETE(req("DELETE", { cookie: sessionCookie }))).status, 403);
  assert.equal((await DELETE(req("DELETE", { cookie: sessionCookie, "x-csrf-token": csrf }))).status, 200);
  assert.equal((await GET(req("GET", { cookie: sessionCookie }))).status, 401);
});
test("login rejects hostile origin, missing request marker, malformed and oversized JSON", async () => {
  for (const headers of [{ origin: "https://hostile.example" }, { origin: "null" }, { "x-netsentinel-request": "" }, { origin: "http://localhost:3000" }] as Record<string, string>[])
    assert.equal((await POST(req("POST", headers, JSON.stringify({ password })))).status, 403);
  for (const body of ["{", "[]", JSON.stringify({ password, command: "forbidden" }), JSON.stringify({ password: "x".repeat(3000) })])
    assert.equal((await POST(req("POST", {}, body))).status, 400);
  assert.equal((await POST(req("POST", { "content-type": "text/plain" }, JSON.stringify({ password })))).status, 400);
});
test("missing configuration and privilege-key reuse fail closed", () => {
  process.env.NETSENTINEL_OPERATOR_PASSWORD = "short";
  assert.equal(login("short").status, 503);
  process.env.NETSENTINEL_OPERATOR_PASSWORD = process.env.NETSENTINEL_READ_TOKEN;
  assert.equal(login(process.env.NETSENTINEL_READ_TOKEN).status, 503);
  process.env.NETSENTINEL_OPERATOR_PASSWORD = password;
});
test("tampering, expiry, duplicate cookie and credential rotation invalidate sessions", () => {
  const now = Date.now();
  const result = login(password, now);
  const cookie = `${SESSION_COOKIE}=${result.token}`;
  assert.ok(localSession(req("GET", { cookie }), now));
  assert.equal(localSession(req("GET", { cookie: `${cookie}; ${cookie}` }), now), null);
  assert.equal(localSession(req("GET", { cookie: `${SESSION_COOKIE}=${"0".repeat(64)}` }), now), null);
  process.env.NETSENTINEL_OPERATOR_PASSWORD = "different-fixture-operator-password-1234";
  assert.equal(localSession(req("GET", { cookie }), now), null);
  process.env.NETSENTINEL_OPERATOR_PASSWORD = password;
  assert.equal(localSession(req("GET", { cookie }), now + SESSION_SECONDS * 1000), null);
});
test("bounded sessions evict oldest and five failed attempts throttle for a minute", () => {
  const now = Date.now() + SESSION_SECONDS * 1000 + 1;
  const first = login(password, now);
  for (let i = 0; i < 16; i++) assert.equal(login(password, now + i).status, 200);
  assert.equal(localSession(req("GET", { cookie: `${SESSION_COOKIE}=${first.token}` }), now + 16), null);
  for (let i = 0; i < 5; i++) assert.equal(login("wrong", now + 20 + i).status, 401);
  assert.equal(login(password, now + 30).status, 429);
  assert.equal(login(password, now + 60_025).status, 200);
});
