"use client";
import { useEffect, useState } from "react";
import { decodePage, decodeSession, pollDelay, type Page, type Sample, type Selection, type Window, type CaptureStatus, type Session, type AnomalyResult } from "./contracts";
import { retainOnError, type Result } from "./poll-result";

type Snapshot = {
  health: Result<boolean>;
  telemetry: Result<Page<Sample>>;
  windows: Result<Page<Window>>;
  capture: Result<Page<CaptureStatus>>;
  session: Result<Session>;
  anomalies: Result<Page<AnomalyResult>>;
  loaded: boolean;
  paused: boolean;
  now: number;
};
async function read<T>(resource: string, selection: Selection, signal: AbortSignal, decode: (data: unknown) => T): Promise<Result<T>> {
  try {
    const query = new URLSearchParams({ session_id: selection.session, mode: selection.mode });
    const response = await fetch(`/api/backend/${resource}?${query}`, { signal, cache: "no-store" });
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.error === "string" ? body.error : `API error ${response.status}`);
    return { data: decode(body) };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Request failed." };
  }
}
export function useMonitor(selection: Selection): Snapshot {
  const [state, setState] = useState<Snapshot>({ health: {}, telemetry: {}, windows: {}, capture: {}, session: {}, anomalies: {}, loaded: false, paused: false, now: 0 });
  useEffect(() => {
    let disposed = false, active = false, failures = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | undefined;
    async function poll() {
      if (disposed || active || document.hidden) return;
      active = true;
      controller = new AbortController();
      const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(7000)]);
      const [health, telemetry, windows, capture, session, anomalies] = await Promise.all([
        read("health", selection, signal, (data) => {
          if (!data || typeof data !== "object" || !("status" in data) || data.status !== "ok" || !("database" in data) || data.database !== "reachable") throw new Error("Backend reports unavailable.");
          return true;
        }),
        read("telemetry", selection, signal, (data) => decodePage<Sample>(data, "telemetry", selection)),
        read("windows", selection, signal, (data) => decodePage<Window>(data, "windows", selection)),
        read("capture-status", selection, signal, (data) => decodePage<CaptureStatus>(data, "capture-status", selection)),
        read("monitoring-sessions", selection, signal, (data) => decodeSession(data, selection)),
        read("anomaly-results", selection, signal, (data) => decodePage<AnomalyResult>(data, "anomaly-results", selection)),
      ]);
      active = false;
      if (disposed) return;
      if (!controller.signal.aborted) {
        failures = health.error || telemetry.error || windows.error || capture.error || session.error || anomalies.error ? failures + 1 : 0;
        // Health is current connectivity, never retained. Data stays historical on errors.
        setState((previous) => ({ health,
          telemetry: retainOnError(previous.telemetry, telemetry),
          windows: retainOnError(previous.windows, windows),
          capture: retainOnError(previous.capture, capture),
          session: retainOnError(previous.session, session),
          anomalies: retainOnError(previous.anomalies, anomalies),
          loaded: true, paused: document.hidden, now: Date.now(),
        }));
      }
      if (!document.hidden) timer = setTimeout(poll, pollDelay(failures));
    }
    function resume() {
      clearTimeout(timer);
      setState((previous) => ({ ...previous, paused: document.hidden, now: Date.now() }));
      if (document.hidden) controller?.abort();
      else if (!active) { failures = 0; void poll(); }
    }
    const clock = setInterval(() => setState((previous) => ({ ...previous, now: Date.now() })), 1000);
    document.addEventListener("visibilitychange", resume);
    window.addEventListener("online", resume);
    void poll();
    return () => { disposed = true; clearTimeout(timer); clearInterval(clock); controller?.abort(); document.removeEventListener("visibilitychange", resume); window.removeEventListener("online", resume); };
  }, [selection]);
  return state;
}
