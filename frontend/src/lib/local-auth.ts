// Server-only: never import this module into a client component/public export.
import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { localRequest } from "./gateway";

export const SESSION_COOKIE = "netsentinel_local_session";
export const SESSION_SECONDS = 4 * 60 * 60;
type Session = { expires: number; csrf: string; configuration: string };
type Store = { sessions: Map<string, Session>; failures: number[] };
const runtime = globalThis as typeof globalThis & { __netsentinelLocalAuth?: Store };
const store: Store = runtime.__netsentinelLocalAuth ??= { sessions: new Map<string, Session>(), failures: [] as number[] };
const hash = (value: string) => createHash("sha256").update(value).digest("hex");
const equals = (a: string, b: string) => timingSafeEqual(Buffer.from(hash(a), "hex"), Buffer.from(hash(b), "hex"));
export function validSecret(value: string | undefined): value is string {
  return typeof value === "string" && value.length >= 32 && value.length <= 256
    && /^[\x21-\x7e]+$/.test(value) && !value.startsWith("replace-with-");
}
function configuration() {
  const password = process.env.NETSENTINEL_OPERATOR_PASSWORD;
  const read = process.env.NETSENTINEL_READ_TOKEN;
  if (!validSecret(password) || !validSecret(read) || password === read) return null;
  return hash(`${password}\0${read}`);
}
function sweep(now: number) {
  for (const [key, value] of store.sessions) if (value.expires <= now) store.sessions.delete(key);
  store.failures = store.failures.filter((time) => time > now - 60_000);
}
function cookieKey(request: Request) {
  const raw = request.headers.get("cookie") ?? "";
  if (raw.length > 4096) return null;
  const matches = raw.split(";").map((part) => part.trim()).filter((part) => part.startsWith(`${SESSION_COOKIE}=`));
  if (matches.length !== 1) return null;
  const value = matches[0].slice(SESSION_COOKIE.length + 1);
  return /^[a-f0-9]{64}$/.test(value) ? hash(value) : null;
}
export function localSession(request: Request, now = Date.now()): Session | null {
  if (!localRequest(request)) return null;
  sweep(now);
  const fingerprint = configuration();
  const key = cookieKey(request);
  const session = key ? store.sessions.get(key) : undefined;
  return fingerprint && session?.configuration === fingerprint && session.expires > now ? session : null;
}
export function login(password: unknown, now = Date.now()): { status: number; token?: string; csrf?: string } {
  sweep(now);
  const fingerprint = configuration();
  if (!fingerprint) return { status: 503 };
  if (store.failures.length >= 5) return { status: 429 };
  if (typeof password !== "string" || password.length > 256 || !equals(password, process.env.NETSENTINEL_OPERATOR_PASSWORD!)) {
    store.failures.push(now);
    return { status: 401 };
  }
  if (store.sessions.size >= 16) store.sessions.delete(store.sessions.keys().next().value!);
  const token = randomBytes(32).toString("hex");
  const csrf = randomBytes(32).toString("hex");
  store.sessions.set(hash(token), { csrf, expires: now + SESSION_SECONDS * 1000, configuration: fingerprint });
  return { status: 200, token, csrf };
}
export function logout(request: Request) {
  const key = cookieKey(request);
  if (key) store.sessions.delete(key);
}
export function localMutation(request: Request): boolean {
  return localRequest(request)
    && request.headers.get("origin") === `http://${request.headers.get("host")}`
    && request.headers.get("x-netsentinel-request") === "local-ui-v1";
}
export function validCSRF(request: Request): boolean {
  const session = localSession(request);
  const supplied = request.headers.get("x-csrf-token") ?? "";
  return !!session && supplied.length === 64 && equals(session.csrf, supplied);
}
export async function boundedJSON(request: Request): Promise<unknown> {
  if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json") throw new Error("json_required");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("body_required");
  let length = 0;
  const chunks: Uint8Array[] = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > 2048) { await reader.cancel(); throw new Error("body_too_large"); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}
