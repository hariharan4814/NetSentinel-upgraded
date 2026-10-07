import { localRequest, upstreamURL, READ_RESOURCES } from "@/lib/gateway";
import { localSession, validSecret } from "@/lib/local-auth";

export const dynamic = "force-dynamic";
const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store" } });

export async function GET(request: Request, context: { params: Promise<{ resource: string }> }) {
  if (!localRequest(request)) return reply({ error: "Local same-origin clients only." }, 403);
  const { resource } = await context.params;
  if (!READ_RESOURCES.includes(resource)) return reply({ error: "Unknown resource." }, 404);
  if (!localSession(request)) return reply({ error: "Sign in to the local monitor." }, 401);
  const readToken = process.env.NETSENTINEL_READ_TOKEN;
  if (!validSecret(readToken)) return reply({ error: "Local read credential is not configured." }, 503);
  let target: URL;
  try { target = upstreamURL(process.env.BACKEND_API_BASE_URL, resource, new URL(request.url).searchParams); }
  catch (error) { return reply({ error: error instanceof Error ? error.message : "Invalid configuration." }, 400); }
  try {
    // Explicit GET only. Never forward browser headers, cookies, arbitrary URLs or mutations.
    const upstream = await fetch(target, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(4000), headers: { Accept: "application/json", Authorization: `Bearer ${readToken}` } });
    if (!upstream.ok) return reply({ error: resource === "monitoring-sessions" && upstream.status === 404
      ? "Session unavailable: no matching session and mode." : `Backend request failed (HTTP ${upstream.status}).` }, upstream.status);
    if (!upstream.headers.get("content-type")?.includes("application/json")) return reply({ error: "Backend returned a non-JSON response." }, 502);
    return reply(await upstream.json());
  } catch { return reply({ error: "Backend unavailable or request timed out." }, 503); }
}
