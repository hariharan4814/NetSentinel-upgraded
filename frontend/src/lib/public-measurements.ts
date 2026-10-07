import type { ConfigOptions, MeasurementType, PhaseChangePayload, Results } from "@cloudflare/speedtest";

export const SPEED_VERSION = 1;
export const SPEED_HISTORY_KEY = "netsentinel.speed-history.v1";
export const SPEED_MAX_MS = 45_000;
export const SPEED_HISTORY_AGE = 30 * 86_400_000;
export const SPEED_HISTORY_LIMIT = 30;
export const SPEED_PLANNED_BYTES = 15_500_000;
// Engine 1.14.1 retries HTTP 429 at most three times per request. This upper
// bound includes those attempts, not protocol headers or retransmissions.
export const SPEED_MAX_ATTEMPT_BYTES = SPEED_PLANNED_BYTES * 4;
export const speedConfig: ConfigOptions = {
  autoStart: false, includeCredentials: false,
  downloadApiUrl: "https://speed.cloudflare.com/__down",
  uploadApiUrl: "https://speed.cloudflare.com/__up",
  logAimApiUrl: null, logMeasurementApiUrl: null,
  measureDownloadLoadedLatency: false, measureUploadLoadedLatency: false,
  bandwidthAbortRequestDuration: 12_000,
  bandwidthFinishRequestDuration: 1_000,
  bandwidthMinRequestDuration: 10,
  measurements: [
    { type: "latency", numPackets: 6 },
    { type: "download", bytes: 1_000_000, count: 1 },
    { type: "download", bytes: 5_000_000, count: 2 },
    { type: "upload", bytes: 500_000, count: 1 },
    { type: "upload", bytes: 2_000_000, count: 2 },
  ],
};

export type SpeedResult = {
  id: string; at: string; version: 1; scope: "LIVE"; source: "Cloudflare edge";
  status: "complete" | "cancelled" | "failed" | "timed-out";
  downloadMbps: number | null; uploadMbps: number | null;
  latencyMs: number | null; jitterMs: number | null; latencySamples: number[];
  receivedBodyBytes: number | null; confirmedUploadBytes: number;
  accountingIncomplete: boolean; durationMs: number;
};
export type SpeedProgress = { stage: string; completedSamples: number; receivedBodyBytes: number | null; confirmedUploadBytes: number };
type Resource = Pick<PerformanceResourceTiming, "name" | "decodedBodySize" | "responseEnd">;
export type SpeedEngine = {
  results: Pick<Results, "getUnloadedLatencyPoints" | "getDownloadBandwidthPoints" | "getUploadBandwidthPoints">;
  onPhaseChange: (phase: PhaseChangePayload) => void;
  onResultsChange: (payload: { type: MeasurementType }) => void; onFinish: (results: Results) => void;
  onError: (message: string) => void; play(): void; pause(): void;
};
export function meanJitter(samples: number[]): number | null {
  if (samples.length < 2) return null;
  return samples.slice(1).reduce((sum, x, i) => sum + Math.abs(x - samples[i]), 0) / (samples.length - 1);
}
export function median(samples: number[]): number | null {
  if (!samples.length) return null;
  const sorted = [...samples].sort((a, b) => a - b), mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
export function payloadMbps(points: { bytes: number; duration: number }[]): number | null {
  const valid = points.filter(p => Number.isFinite(p.bytes) && p.bytes > 0 && Number.isFinite(p.duration) && p.duration >= 10);
  return valid.length ? valid.reduce((n, p) => n + p.bytes * 8, 0) / valid.reduce((n, p) => n + p.duration, 0) / 1000 : null;
}
export function summarizeSpeed(results: SpeedEngine["results"], entries: Resource[], status: SpeedResult["status"], durationMs: number): SpeedResult {
  const down = results.getDownloadBandwidthPoints(), up = results.getUploadBandwidthPoints();
  const latencySamples = results.getUnloadedLatencyPoints().filter(x => Number.isFinite(x) && x >= 0).slice(0, 6);
  const resources = entries.filter(e => {
    try { const u = new URL(e.name); return u.origin === "https://speed.cloudflare.com" && u.pathname === "/__down" && Number(u.searchParams.get("bytes")) > 0; } catch { return false; }
  });
  const bytesAvailable = resources.length > 0 && resources.every(e => Number.isFinite(e.decodedBodySize) && e.decodedBodySize > 0);
  // Never use the engine's estimated 0.5% header overhead as measured bytes.
  // Only accepted body lengths are eligible for a throughput result.
  const pool = [...resources];
  const verifiedDown = down.filter(p => {
    const index = pool.findIndex(e => e.decodedBodySize === p.bytes && Number(new URL(e.name).searchParams.get("bytes")) === p.bytes);
    if (index < 0) return false;
    pool.splice(index, 1); return true;
  });
  const receivedBodyBytes = bytesAvailable ? resources.reduce((n, p) => n + p.decodedBodySize, 0) : null;
  return {
    id: crypto.randomUUID(), at: new Date().toISOString(), version: SPEED_VERSION,
    source: "Cloudflare edge", scope: "LIVE", status,
    downloadMbps: payloadMbps(verifiedDown), uploadMbps: payloadMbps(up),
    latencyMs: median(latencySamples), jitterMs: meanJitter(latencySamples), latencySamples,
    receivedBodyBytes, confirmedUploadBytes: up.reduce((n, p) => n + p.bytes, 0),
    accountingIncomplete: status !== "complete" || !bytesAvailable || verifiedDown.length !== down.length || resources.length !== down.length,
    durationMs: Math.max(0, durationMs),
  };
}

export async function runSpeedTest(options: {
  signal: AbortSignal; onProgress: (progress: SpeedProgress) => void;
  engineFactory?: (config: ConfigOptions) => Promise<SpeedEngine>;
  resources?: () => Resource[]; clock?: () => number; timeoutMs?: number;
}): Promise<SpeedResult> {
  options.signal.throwIfAborted();
  const factory = options.engineFactory ?? (async config => {
    const { default: Engine } = await import("@cloudflare/speedtest");
    return new Engine(config) as SpeedEngine;
  });
  const engine = await factory(speedConfig);
  options.signal.throwIfAborted();
  const clock = options.clock ?? (() => performance.now());
  const resources = options.resources ?? (() => performance.getEntriesByType("resource") as PerformanceResourceTiming[]);
  const started = clock();
  let stage = "Latency";
  return new Promise(resolve => {
    let ended = false;
    const finish = (status: SpeedResult["status"]) => {
      if (ended) return;
      ended = true; clearTimeout(timer); options.signal.removeEventListener("abort", cancel);
      engine.pause();
      resolve(summarizeSpeed(engine.results, resources(), status, clock() - started));
    };
    const cancel = () => finish("cancelled");
    const timer = setTimeout(() => finish("timed-out"), Math.min(options.timeoutMs ?? SPEED_MAX_MS, SPEED_MAX_MS));
    options.signal.addEventListener("abort", cancel, { once: true });
    engine.onPhaseChange = ({ measurement }) => { stage = measurement.type === "latency" ? "Latency" : measurement.type === "download" ? "Download" : "Upload"; progress(); };
    function progress() {
      if (ended) return;
      const current = summarizeSpeed(engine.results, resources(), "cancelled", clock() - started);
      options.onProgress({ stage, completedSamples: current.latencySamples.length + engine.results.getDownloadBandwidthPoints().length + engine.results.getUploadBandwidthPoints().length,
        receivedBodyBytes: current.receivedBodyBytes, confirmedUploadBytes: current.confirmedUploadBytes });
    }
    engine.onResultsChange = progress;
    engine.onFinish = () => finish("complete");
    engine.onError = () => finish("failed");
    try { engine.play(); } catch { finish("failed"); }
  });
}

const finite = (v: unknown, max: number) => typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= max;
export function parseSpeedHistory(raw: string | null, now = Date.now()): SpeedResult[] {
  if (!raw || raw.length > 100_000) return [];
  try {
    const data: unknown = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    const ids = new Set<string>();
    return data.slice(0, 100).flatMap((v): SpeedResult[] => {
      if (!v || typeof v !== "object") return [];
      const r = v as SpeedResult, at = Date.parse(r.at);
      if (typeof r.id !== "string" || !/^[a-f0-9-]{36}$/i.test(r.id) || ids.has(r.id) || !Number.isFinite(at) || at > now + 1000 || at < now - SPEED_HISTORY_AGE || r.version !== SPEED_VERSION || r.scope !== "LIVE" || r.source !== "Cloudflare edge" || r.status !== "complete") return [];
      if (![r.downloadMbps, r.uploadMbps].every(v => v === null || finite(v, 1e6)) || ![r.latencyMs, r.jitterMs].every(v => v === null || finite(v, SPEED_MAX_MS)) || !(r.receivedBodyBytes === null || finite(r.receivedBodyBytes, SPEED_MAX_ATTEMPT_BYTES)) || !finite(r.confirmedUploadBytes, SPEED_MAX_ATTEMPT_BYTES) || !finite(r.durationMs, 60_000) || typeof r.accountingIncomplete !== "boolean" || !Array.isArray(r.latencySamples) || r.latencySamples.length > 6 || !r.latencySamples.every(v => finite(v, SPEED_MAX_MS))) return [];
      ids.add(r.id);
      return [{ id: r.id, at: r.at, version: SPEED_VERSION, scope: "LIVE", source: "Cloudflare edge", status: "complete", downloadMbps: r.downloadMbps, uploadMbps: r.uploadMbps, latencyMs: r.latencyMs, jitterMs: r.jitterMs, latencySamples: [...r.latencySamples], receivedBodyBytes: r.receivedBodyBytes, confirmedUploadBytes: r.confirmedUploadBytes, accountingIncomplete: r.accountingIncomplete, durationMs: r.durationMs }];
    }).sort((a, b) => Date.parse(b.at) - Date.parse(a.at)).slice(0, SPEED_HISTORY_LIMIT);
  } catch { return []; }
}

export type NetworkDetails = { at: string; source: "ipwho.is"; ip: string; family: "IPv4" | "IPv6"; organization: string | null; asn: string | null; city: string | null; region: string | null; country: string | null };
const field = (v: unknown) => typeof v === "string" && v.trim() ? v.replace(/[\u0000-\u001f\u007f]/g, "").slice(0, 160) : null;
export function parseNetworkDetails(value: unknown): NetworkDetails {
  if (!value || typeof value !== "object") throw new Error("The lookup returned an invalid response.");
  const data = value as Record<string, unknown>;
  if (data.success !== true || typeof data.ip !== "string" || data.ip.length > 45) throw new Error("Network details are unavailable from this provider.");
  const isV4 = /^(?:\d{1,3}\.){3}\d{1,3}$/.test(data.ip) && data.ip.split(".").every(n => Number(n) <= 255);
  let isV6 = false;
  if (data.ip.includes(":") && /^[a-f\d:.]+$/i.test(data.ip)) { try { isV6 = new URL(`http://[${data.ip}]/`).hostname.startsWith("["); } catch { /* Invalid IPv6 stays unavailable. */ } }
  if (!isV4 && !isV6) throw new Error("The lookup did not return an IP address.");
  const connection = data.connection && typeof data.connection === "object" ? data.connection as Record<string, unknown> : {};
  return { at: new Date().toISOString(), source: "ipwho.is", ip: data.ip, family: isV4 ? "IPv4" : "IPv6", organization: field(connection.org) ?? field(connection.isp), asn: typeof connection.asn === "number" && Number.isSafeInteger(connection.asn) && connection.asn > 0 ? `AS${connection.asn}` : null, city: field(data.city), region: field(data.region), country: field(data.country) };
}
export async function lookupNetwork(signal: AbortSignal, fetcher: typeof fetch = fetch): Promise<NetworkDetails> {
  const response = await fetcher("https://ipwho.is/?fields=success,ip,type,city,region,country,connection", { signal: AbortSignal.any([signal, AbortSignal.timeout(8000)]), credentials: "omit", cache: "no-store", redirect: "error", referrerPolicy: "no-referrer" });
  if (response.status === 429) throw new Error("The lookup provider’s daily limit was reached. Try again tomorrow; no automatic retry will be made.");
  if (!response.ok || !response.headers.get("content-type")?.includes("json")) throw new Error("The lookup service is unavailable. You can still use the other tools.");
  if (!response.body) throw new Error("The lookup returned no data.");
  const reader = response.body.getReader(); const chunks: Uint8Array[] = []; let size = 0;
  try {
    while (true) { const { done, value } = await reader.read(); if (done) break; size += value.byteLength; if (size > 16_384) throw new Error("The lookup response was too large."); chunks.push(value); }
  } finally { await reader.cancel(); }
  const joined = new Uint8Array(size); let offset = 0; for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.length; }
  return parseNetworkDetails(JSON.parse(new TextDecoder().decode(joined)));
}
