// Server-only, fixed local job endpoints; never relay worker credentials or arbitrary paths.
import { boundedJSON, localMutation, localSession, validCSRF, validSecret } from "./local-auth";
import { localRequest } from "./gateway";
import { UUID } from "./contracts";
import { validLabConfig } from "./lab-contract";

const MAX_RESPONSE = 4 * 1024 * 1024;
const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
export function labUpstream(base: string | undefined, id?: string, cancel = false): URL {
  if (!base || (id !== undefined && !UUID.test(id)) || (cancel && !id)) throw new Error("Invalid local lab configuration.");
  const url = new URL(base);
  if (url.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) || url.username || url.password || url.search || url.hash || url.pathname !== "/api/v1/") throw new Error("Invalid local lab configuration.");
  url.pathname += `lab/jobs/${id ? `${id.toLowerCase()}/` : ""}${cancel ? "cancel/" : ""}`;
  return url;
}
export async function labRelay(request: Request, id?: string, cancel = false): Promise<Response> {
  if (!localRequest(request)) return reply({ error: "Local same-origin clients only." }, 403);
  if (!localSession(request)) return reply({ error: "Sign in to the local lab." }, 401);
  const mutation = request.method === "POST";
  if ((request.method !== "GET" && !mutation) || (cancel && !mutation)) return reply({ error: "Unsupported job action." }, 405);
  if (mutation && (!localMutation(request) || !validCSRF(request))) return reply({ error: "Authenticated same-origin action and CSRF token required." }, 403);
  if (new URL(request.url).search || (id !== undefined && !UUID.test(id))) return reply({ error: "Invalid job identifier or query." }, 400);
  if (mutation && id && !cancel) return reply({ error: "Unsupported job action." }, 405);
  let body: string | undefined;
  if (mutation) {
    try {
      const value = await boundedJSON(request);
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error();
      if (cancel ? Object.keys(value).length !== 0 : Object.keys(value).join() !== "config" || !validLabConfig((value as { config: unknown }).config)) throw new Error();
      body = JSON.stringify(value);
    } catch { return reply({ error: "Provide only bounded experiment settings as JSON (at most 2048 bytes)." }, 400); }
  }
  const token = mutation ? process.env.NETSENTINEL_LAB_TOKEN : process.env.NETSENTINEL_READ_TOKEN;
  if (!validSecret(token) || (mutation && [process.env.NETSENTINEL_READ_TOKEN, process.env.NETSENTINEL_OPERATOR_PASSWORD, process.env.NETSENTINEL_LAB_WORKER_TOKEN, process.env.NETSENTINEL_INGEST_TOKEN, process.env.NETSENTINEL_MODEL_TOKEN].includes(token))) return reply({ error: "Local lab credentials are not configured. See the AI Lab setup guide." }, 503);
  let url: URL;
  try { url = labUpstream(process.env.BACKEND_API_BASE_URL, id, cancel); }
  catch { return reply({ error: "Local lab backend is not configured." }, 503); }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10_000);
  const abort = () => controller.abort();
  request.signal.addEventListener("abort", abort, { once: true });
  try {
    if (request.signal.aborted) controller.abort();
    const upstream = await fetch(url, { method: request.method, body, headers: { Authorization: `Bearer ${token}`, Accept: "application/json", ...(mutation ? { "Content-Type": "application/json" } : {}) }, redirect: "error", cache: "no-store", signal: controller.signal });
    if (!upstream.ok) {
      await upstream.body?.cancel();
      const status = [400, 404, 409, 429].includes(upstream.status) ? upstream.status : 502;
      return reply({ error: status === 404 ? "Experiment is no longer retained." : status === 409 || status === 429 ? "The lab queue is full or this job can no longer change. Refresh its status." : "The local lab could not complete this request. Check the backend and worker." }, status);
    }
    if (upstream.headers.get("content-type")?.split(";")[0].trim() !== "application/json") throw new Error();
    const reader = upstream.body?.getReader();
    if (!reader) throw new Error();
    let size = 0;
    const chunks: Uint8Array[] = [];
    try {
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > MAX_RESPONSE) { await reader.cancel(); throw new Error(); }
        chunks.push(part.value);
      }
    } finally { reader.releaseLock(); }
    return reply(JSON.parse(Buffer.concat(chunks).toString("utf8")), upstream.status);
  } catch { return reply({ error: "Lab connection unavailable or response invalid. Saved experiments are unchanged." }, 502); }
  finally { clearTimeout(timer); request.signal.removeEventListener("abort", abort); }
}
