/** Public browser measurements. Independent of private sensor/ML contracts. */
export const CHECK_VERSION = "browser-http-v1" as const;
export const PROBE_COUNT = 8;
export const TIMEOUT_MS = 3000;
export const HISTORY_KEY = "netsentinel.connection-history.v1";
export const MAX_HISTORY = 10;
export const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
export type Scope = "LIVE" | "LOCAL";
export type Probe = { ms: number | null };
export type Check = {
  id: string; at: string; scope: Scope; version: typeof CHECK_VERSION; probes: Probe[];
};

export function measurementScope(hostname: string): Scope {
  const host = hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (host === "localhost" || host.endsWith(".localhost") || host === "::1"
    || host.endsWith(".local") || !host.includes(".") || host.includes(":")) return "LOCAL";
  // Conservatively classify literal IP hosts as local: public release uses HTTPS DNS.
  return /^\d+\.\d+\.\d+\.\d+$/.test(host) ? "LOCAL" : "LIVE";
}

export function summarize(probes: Probe[]) {
  const values = probes.flatMap(p => p.ms === null ? [] : [p.ms]).sort((a, b) => a - b);
  const middle = Math.floor(values.length / 2);
  const median = values.length ? (values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2) : null;
  const spread = values.length > 1 ? values.at(-1)! - values[0] : null;
  return { median, spread, success: values.length, failed: probes.length - values.length, total: probes.length };
}

export function interpretation(check: Check) {
  const stats = summarize(check.probes);
  if (check.scope === "LOCAL") return { title: "Local check complete", tone: "neutral", detail: "These requests target this local app. They cannot tell you how your internet is performing. Use the published site for an internet check." };
  if (!stats.success) return { title: "This site didn’t respond", tone: "warning", detail: "None of the eight requests completed. Try another website. A connection problem, this site, a VPN or a browser restriction could be responsible." };
  if (stats.failed) return { title: "Some requests didn’t complete", tone: "warning", detail: `${stats.failed} of ${stats.total} requests failed or timed out. Repeat the check, then compare another website before drawing a conclusion.` };
  if (stats.median! >= 300 || stats.spread! >= 150) return { title: "Responses were slow or variable", tone: "warning", detail: "This short check crossed our advisory threshold: a typical response of 300 ms or a range of 150 ms. Try one change below, then compare a new check." };
  return { title: "This site responded consistently", tone: "good", detail: "All eight requests completed within our advisory range. This is a short snapshot of one website; other apps or connections can still have problems." };
}

export async function runCheck(options: {
  signal: AbortSignal; onProgress: (probes: Probe[]) => void;
  fetcher?: typeof fetch; pauseMs?: number;
}): Promise<Probe[]> {
  const probes: Probe[] = [];
  const fetcher = options.fetcher ?? fetch;
  for (let i = 0; i < PROBE_COUNT; i++) {
    options.signal.throwIfAborted();
    const started = performance.now();
    let ms: number | null = null;
    try {
      const response = await fetcher(`/connection-check.json?check=${crypto.randomUUID()}`, {
        cache: "no-store", credentials: "omit", redirect: "error",
        signal: AbortSignal.any([options.signal, AbortSignal.timeout(TIMEOUT_MS)]),
      });
      if (!response.ok || !response.headers.get("content-type")?.includes("application/json")) throw new Error("Unexpected response");
      const data: unknown = await response.json();
      if (!data || typeof data !== "object" || !("service" in data) || data.service !== "netsentinel-connectivity"
        || !("version" in data) || data.version !== 1) throw new Error("Unexpected response");
      const elapsed = performance.now() - started;
      // Background stalls and scheduling delays beyond our deadline are failures.
      if (elapsed <= TIMEOUT_MS) ms = Math.round(elapsed * 10) / 10;
    } catch { /* A failed HTTP request stays missing, never a zero-time success. */ }
    options.signal.throwIfAborted();
    probes.push({ ms });
    options.onProgress([...probes]);
    if (i < PROBE_COUNT - 1) await new Promise<void>((resolve, reject) => {
      const abort = () => { clearTimeout(timer); reject(options.signal.reason); };
      const timer = setTimeout(() => { options.signal.removeEventListener("abort", abort); resolve(); }, options.pauseMs ?? 450);
      options.signal.addEventListener("abort", abort, { once: true });
      if (options.signal.aborted) { options.signal.removeEventListener("abort", abort); abort(); }
    });
  }
  return probes;
}

export function parseHistory(raw: string | null, now = Date.now()): Check[] {
  if (!raw || raw.length > 30000) return [];
  try {
    const data: unknown = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    const ids = new Set<string>();
    return data.filter((item): item is Check => {
      if (!item || typeof item !== "object" || !/^[a-f0-9-]{36}$/i.test(item.id)
        || item.version !== CHECK_VERSION || !["LIVE", "LOCAL"].includes(item.scope)
        || typeof item.at !== "string" || !Number.isFinite(Date.parse(item.at))
        || Date.parse(item.at) > now || now - Date.parse(item.at) > MAX_AGE_MS
        || !Array.isArray(item.probes) || item.probes.length !== PROBE_COUNT
        || !item.probes.every((p: Probe) => p && (p.ms === null || (typeof p.ms === "number" && Number.isFinite(p.ms) && p.ms >= 0 && p.ms <= TIMEOUT_MS)))
        || ids.has(item.id)) return false;
      ids.add(item.id);
      return true;
    }).sort((a, b) => Date.parse(b.at) - Date.parse(a.at)).slice(0, MAX_HISTORY)
      .map(({ id, at, scope, probes }) => ({ id, at, scope, version: CHECK_VERSION, probes: probes.map(p => ({ ms: p.ms })) }));
  } catch { return []; }
}

export function transferSeconds(size: number, unit: "MB" | "GB", mbps: number): number | null {
  if (!Number.isFinite(size) || !Number.isFinite(mbps) || size <= 0 || size > 100000 || mbps <= 0 || mbps > 100000) return null;
  return size * (unit === "GB" ? 1000 : 1) * 8 / mbps;
}

export function formatDuration(seconds: number) {
  if (seconds < 1) return "Less than a second";
  if (seconds < 60) return `${Math.ceil(seconds)} seconds`;
  if (seconds < 3600) return `${Math.ceil(seconds / 60)} minutes`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)} hours`;
  return `${(seconds / 86400).toFixed(1)} days`;
}

export function supportReport(check: Check) {
  const stats = summarize(check.probes);
  return ["NETSENTINEL — CONNECTION CHECK", `Observed (UTC): ${check.at}`, `Source: ${check.scope} browser HTTP check`,
    `Method: ${check.version}; eight requests to the NetSentinel site; ${TIMEOUT_MS} ms timeout per request.`,
    `Requests answered: ${stats.success}/${stats.total}`, `Median HTTP response: ${stats.median === null ? "unavailable" : `${stats.median.toFixed(1)} ms`}`,
    `Response range: ${stats.spread === null ? "unavailable" : `${stats.spread.toFixed(1)} ms`}`, interpretation(check).title,
    interpretation(check).detail, "", ...check.probes.map((p, i) => `Request ${i + 1}: ${p.ms === null ? "failed or timed out" : `${p.ms} ms`}`), "",
    "LIMITS: One website, one short interval. HTTP times include browser and server overhead. This does not measure download/upload speed, ICMP ping, Wi-Fi strength or packet loss. It cannot identify the cause of a failure or certify network security.",
    "Advisory thresholds: median >= 300 ms or range >= 150 ms. These are product heuristics, not validated ISP guarantees.",
    "No packet captures, IP addresses, account details or browsing history are included.",
  ].join("\n");
}
