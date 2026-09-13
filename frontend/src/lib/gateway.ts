import { MODES, UUID } from "./contracts";
export const READ_RESOURCES = ["health", "telemetry", "windows", "capture-status", "monitoring-sessions"];

export function localRequest(request: Request): boolean {
  try {
    const url = new URL(request.url);
    const host = request.headers.get("host");
    const origin = request.headers.get("origin");
    // NextURL normalizes loopback names to localhost, but preserves the wire Host.
    // Validate that authority first; never use forwarded headers as trusted input.
    if (!host || !/^(localhost|127\.0\.0\.1|\[::1\])(?::[1-9]\d{0,4})?$/i.test(host)) return false;
    const authority = new URL(`http://${host}`);
    if (url.protocol !== "http:" || url.username || url.password
        || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
        || url.port !== authority.port
        || (url.hostname !== authority.hostname && url.hostname !== "localhost")) return false;
    // These names are not interchangeable browser origins, despite Next normalization.
    if (origin !== null && origin !== authority.origin) return false;
    const referer = request.headers.get("referer");
    if (referer !== null) {
      const source = new URL(referer);
      if (source.origin !== authority.origin || source.username || source.password) return false;
    }
    const site = request.headers.get("sec-fetch-site");
    return site === null || site === "same-origin" || site === "none";
  } catch { return false; }
}
export function upstreamURL(base: string | undefined, resource: string, query: URLSearchParams): URL {
  if (!READ_RESOURCES.includes(resource)) throw new Error("Unknown resource.");
  if (!base) throw new Error("Configure BACKEND_API_BASE_URL in frontend/.env.local.");
  const url = new URL(base);
  if (url.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)
      || url.username || url.password || url.search || url.hash || url.pathname !== "/api/v1/") {
    throw new Error("BACKEND_API_BASE_URL must be a loopback HTTP URL ending in /api/v1/ without credentials.");
  }
  url.pathname += `${resource}/`;
  if (resource !== "health") {
    const session = query.get("session_id") ?? "";
    const mode = query.get("mode") ?? "";
    if (!UUID.test(session) || !(MODES as readonly string[]).includes(mode)) throw new Error("A session UUID and mode are required.");
    url.searchParams.set("session_id", session.toLowerCase());
    url.searchParams.set("mode", mode);
    if (resource !== "monitoring-sessions") url.searchParams.set("limit", resource === "telemetry" ? "60" : "20");
  }
  return url;
}
