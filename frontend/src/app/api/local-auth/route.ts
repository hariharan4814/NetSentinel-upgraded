import { boundedJSON, localMutation, localSession, login, logout, SESSION_COOKIE, SESSION_SECONDS, validCSRF } from "@/lib/local-auth";
import { localRequest } from "@/lib/gateway";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
const reply = (body: unknown, status = 200, extra: Record<string, string> = {}) => Response.json(body, {
  status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...extra },
});
export async function GET(request: Request) {
  if (!localRequest(request)) return reply({ error: "Local same-origin clients only." }, 403);
  const session = localSession(request);
  return session ? reply({ authenticated: true, csrf: session.csrf, expiresAt: new Date(session.expires).toISOString() })
    : reply({ authenticated: false }, 401);
}
export async function POST(request: Request) {
  if (!localMutation(request)) return reply({ error: "Same-origin local JSON action required." }, 403);
  let payload: unknown;
  try { payload = await boundedJSON(request); } catch { return reply({ error: "A JSON password object of at most 2048 bytes is required." }, 400); }
  if (!payload || typeof payload !== "object" || Array.isArray(payload) || Object.keys(payload).join() !== "password") return reply({ error: "Only password is accepted." }, 400);
  const result = login((payload as { password: unknown }).password);
  if (!result.token) return reply({ error: result.status === 503 ? "Local operator authentication is not configured. See docs/LOCAL_AUTH.md."
    : result.status === 429 ? "Too many attempts. Wait one minute before trying again." : "The local operator password was not accepted." }, result.status,
  result.status === 429 ? { "Retry-After": "60" } : {});
  // HTTP is allowed only on loopback; Secure cookies require a separately designed HTTPS deployment.
  return reply({ authenticated: true, csrf: result.csrf }, 200, {
    "Set-Cookie": `${SESSION_COOKIE}=${result.token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${SESSION_SECONDS}`,
  });
}
export async function DELETE(request: Request) {
  if (!localMutation(request) || !validCSRF(request)) return reply({ error: "Local authenticated action required." }, 403);
  logout(request);
  return reply({ authenticated: false }, 200, { "Set-Cookie": `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0` });
}
