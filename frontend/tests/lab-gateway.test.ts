import { test } from "node:test";
import assert from "node:assert/strict";
import { labRelay, labUpstream } from "../src/lib/lab-gateway";
import { login, SESSION_COOKIE } from "../src/lib/local-auth";
import { DEFAULT_LAB_CONFIG, validLabConfig } from "../src/lib/lab-contract";

const password = "lab-test-operator-never-for-runtime-000";
const read = "lab-test-read-token-never-for-runtime-000";
const write = "lab-test-write-token-never-for-runtime-000";
process.env.NETSENTINEL_OPERATOR_PASSWORD = password;
process.env.NETSENTINEL_READ_TOKEN = read;
process.env.NETSENTINEL_LAB_TOKEN = write;
process.env.BACKEND_API_BASE_URL = "http://127.0.0.1:8001/api/v1/";
const session = login(password);
function request(method = "GET", headers: Record<string, string> = {}, body?: string) {
  return new Request("http://127.0.0.1:3000/api/lab/jobs", { method, headers: {
    host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000", cookie: `${SESSION_COOKIE}=${session.token}`,
    "x-netsentinel-request": "local-ui-v1", "x-csrf-token": session.csrf!, "content-type": "application/json", ...headers,
  }, ...(body === undefined ? {} : { body }) });
}
test("lab settings reject extra fields, strings, non-finite and fractional counts", () => {
  assert.ok(validLabConfig(DEFAULT_LAB_CONFIG));
  for (const value of [{ ...DEFAULT_LAB_CONFIG, seed: true }, { ...DEFAULT_LAB_CONFIG, noise: Infinity }, { ...DEFAULT_LAB_CONFIG, seed: 1.5 }, { ...DEFAULT_LAB_CONFIG, command: "anything" }, { ...DEFAULT_LAB_CONFIG, gap_probability: .2 }]) assert.equal(validLabConfig(value), false);
});
test("lab URL is fixed loopback path with UUID only and no credentials or query", () => {
  assert.equal(labUpstream(process.env.BACKEND_API_BASE_URL).pathname, "/api/v1/lab/jobs/");
  for (const base of ["https://example.org/api/v1/", "http://127.0.0.1:8001/", "http://user@localhost/api/v1/", "http://localhost/api/v1/?a=b"]) assert.throws(() => labUpstream(base));
  assert.throws(() => labUpstream(process.env.BACKEND_API_BASE_URL, "../worker"));
});
test("lab relay authenticates and rejects hostile origin, CSRF and large body before fetch", async () => {
  assert.equal((await labRelay(request("GET", { cookie: "" }))).status, 401);
  assert.equal((await labRelay(request("POST", { origin: "https://hostile.example" }, "{}"))).status, 403);
  assert.equal((await labRelay(request("POST", { "x-csrf-token": "wrong" }, "{}"))).status, 403);
  for (const body of ["{}", "[]", "{", JSON.stringify({ config: DEFAULT_LAB_CONFIG, command: "bad" }), " ".repeat(2049)]) assert.equal((await labRelay(request("POST", {}, body))).status, 400);
});
test("lab relay uses separate server tokens, rejects redirects/errors and bounds streamed results", async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async (_url, options) => {
      assert.equal(new Headers(options?.headers).get("Authorization"), `Bearer ${read}`);
      assert.equal(options?.redirect, "error");
      assert.equal(new Headers(options?.headers).get("Cookie"), null);
      return Response.json({ jobs: [] });
    };
    assert.equal((await labRelay(request())).status, 200);
    globalThis.fetch = async (_url, options) => {
      assert.equal(new Headers(options?.headers).get("Authorization"), `Bearer ${write}`);
      assert.deepEqual(JSON.parse(options?.body as string), { config: DEFAULT_LAB_CONFIG });
      return Response.json({ status: "QUEUED" }, { status: 201 });
    };
    assert.equal((await labRelay(request("POST", {}, JSON.stringify({ config: DEFAULT_LAB_CONFIG })))).status, 201);
    globalThis.fetch = async () => new Response("sensitive server exception", { status: 500 });
    const failed = await labRelay(request());
    assert.equal(failed.status, 502); assert.doesNotMatch(await failed.text(), /sensitive/);
    globalThis.fetch = async () => new Response(" ".repeat(4 * 1024 * 1024 + 1), { headers: { "content-type": "application/json" } });
    assert.equal((await labRelay(request())).status, 502);
    process.env.NETSENTINEL_LAB_TOKEN = read;
    assert.equal((await labRelay(request("POST", {}, JSON.stringify({ config: DEFAULT_LAB_CONFIG })))).status, 503);
  } finally { globalThis.fetch = original; process.env.NETSENTINEL_LAB_TOKEN = write; }
});
