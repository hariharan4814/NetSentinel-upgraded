export const MODES = ["LIVE", "SIMULATION", "REPLAY"] as const;
export type Mode = typeof MODES[number];
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export type Selection = { session: string; mode: Mode };
export type Identity = { id: string; session_id: string; run_id: string; interface_name: string; mode: Mode };
export type Sample = Identity & {
  observed_at: string; valid: boolean; reason: string | null;
  upload_bytes_per_second: number | null; download_bytes_per_second: number | null;
  packets_sent: number; packets_received: number;
};
export type Window = Identity & {
  start: string; end: string; valid: boolean; partial: boolean; reason: string | null;
  packets: number; ip_bytes: number; tcp_packets: number; udp_packets: number; flow_count: number;
};
export type Page<T> = { results: T[]; next: string | null };
export type CaptureStatus = Identity & {
  received_at: string; observed_at: string; state: "RUNNING" | "INTERFACE_LOST" | "RECOVERING" | "STOPPED";
  valid: boolean; reason: string | null; loss_started_at: string | null; gap_ended_at: string | null;
  monitoring_gap_seconds: number; recovery_attempts: number;
};
export type Session = Omit<Identity, "id"> & {
  source_id: string; started_at: string; received_at: string; observation_profile: string; schema_version: string;
};

export function decodeSession(value: unknown, selection: Selection): Session {
  const row = record(value);
  if (row.session_id !== selection.session || row.mode !== selection.mode) throw new Error("API provenance mismatch.");
  for (const key of ["source_id", "run_id"]) { text(row[key]); if (!UUID.test(row[key])) throw new Error("Invalid API identity."); }
  for (const key of ["interface_name", "observation_profile", "schema_version"]) text(row[key]);
  timestamp(row.started_at); timestamp(row.received_at);
  return row as unknown as Session;
}

// Status events are not heartbeats: an old state remains historical, not current proof.
export const STATUS_STALE_MS = 15000;
export function statusFreshness(status: CaptureStatus, now: number): string {
  const age = now - Date.parse(status.observed_at);
  return age < 0 ? "Future observation · current state unavailable" : age > STATUS_STALE_MS
    ? "Stale report · current state unavailable" : "Recent report · not a physical link check";
}

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid API response.");
  return value as Record<string, unknown>;
}
function text(value: unknown): asserts value is string {
  if (typeof value !== "string" || !value.length) throw new Error("Invalid API text.");
}
function timestamp(value: unknown): asserts value is string {
  text(value);
  if (!/(Z|[+-]\d\d:\d\d)$/.test(value) || !Number.isFinite(Date.parse(value))) throw new Error("Invalid API timestamp.");
}
function count(value: unknown) {
  if (!Number.isSafeInteger(value) || (value as number) < 0) throw new Error("API count cannot be represented safely.");
}
function rate(value: unknown) {
  if (value !== null && (typeof value !== "number" || !Number.isFinite(value) || value < 0)) throw new Error("Invalid API rate.");
}
export function decodePage<T extends Sample | Window | CaptureStatus>(value: unknown, kind: "telemetry" | "windows" | "capture-status", selection: Selection): Page<T> {
  const page = record(value);
  if (!Array.isArray(page.results) || page.results.length > 60 || (page.next !== null && typeof page.next !== "string")) throw new Error("Invalid API page.");
  for (const item of page.results) {
    const row = record(item);
    if (row.session_id !== selection.session || row.mode !== selection.mode) throw new Error("API provenance mismatch.");
    for (const key of ["id", "run_id"]) { text(row[key]); if (!UUID.test(row[key])) throw new Error("Invalid API identity."); }
    text(row.interface_name);
    if (typeof row.valid !== "boolean" || (row.reason !== null && typeof row.reason !== "string")) throw new Error("Invalid API validity.");
    if (kind === "telemetry") {
      timestamp(row.observed_at); rate(row.upload_bytes_per_second); rate(row.download_bytes_per_second);
      count(row.packets_sent); count(row.packets_received);
      if (row.valid && (row.upload_bytes_per_second === null || row.download_bytes_per_second === null)) throw new Error("Valid sample has missing rates.");
      if (!row.valid && (!row.reason || row.upload_bytes_per_second !== null || row.download_bytes_per_second !== null)) throw new Error("Invalid sample must retain null rates and reason.");
    } else if (kind === "capture-status") {
      timestamp(row.observed_at); timestamp(row.received_at);
      for (const key of ["loss_started_at", "gap_ended_at"]) if (row[key] !== null) timestamp(row[key]);
      if (!["RUNNING", "INTERFACE_LOST", "RECOVERING", "STOPPED"].includes(row.state as string)
          || row.valid !== (row.state === "RUNNING") || (!row.valid && !row.reason)) throw new Error("Invalid capture status.");
      rate(row.monitoring_gap_seconds);
      if (row.monitoring_gap_seconds === null) throw new Error("Missing recorded gap duration.");
      count(row.recovery_attempts);
    } else {
      timestamp(row.start); timestamp(row.end);
      if (typeof row.partial !== "boolean" || row.valid === row.partial || (!row.valid && !row.reason)) throw new Error("Invalid window quality.");
      for (const key of ["packets", "ip_bytes", "tcp_packets", "udp_packets", "flow_count"]) count(row[key]);
    }
  }
  return page as unknown as Page<T>;
}

// Display policy, not a sensor acceptance threshold. LIVE does not imply fresh.
export const STALE_MS = 5000;
export function isFresh(sample: Sample | undefined, now: number): boolean {
  if (!sample) return false;
  const age = now - Date.parse(sample.observed_at);
  return age >= 0 && age <= STALE_MS;
}
export function currentRate(sample: Sample | undefined, direction: "upload" | "download", now: number, available: boolean): number | null {
  return sample?.valid && available && isFresh(sample, now) ? sample[`${direction}_bytes_per_second`] : null;
}
export function pollDelay(failures: number): number { return Math.min(30000, 2000 * 2 ** Math.min(failures, 4)); }
export function formatRate(value: number | null): string {
  if (value === null) return "Unavailable";
  if (value >= 1024 * 1024) return `${(value / 1024 / 1024).toFixed(2)} MiB/s`;
  if (value >= 1024) return `${(value / 1024).toFixed(2)} KiB/s`;
  return `${value.toFixed(1)} B/s`;
}
export function utc(value: string): string { return new Date(value).toISOString().replace("T", " ").replace(".000Z", " UTC").replace("Z", " UTC"); }
