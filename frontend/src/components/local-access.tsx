"use client";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Dashboard } from "./dashboard";

export function LocalAccess({ render, lab = false }: { render?: (csrf: string) => ReactNode; lab?: boolean } = {}) {
  const [csrf, setCSRF] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const check = async () => {
      try {
        const response = await fetch("/api/local-auth", { cache: "no-store", signal: controller.signal });
        const body = await response.json();
        setCSRF(response.ok && typeof body.csrf === "string" ? body.csrf : null);
      } catch { if (!controller.signal.aborted) setError("The local sign-in service is unavailable."); }
      finally { if (!controller.signal.aborted) setChecking(false); }
    };
    void check();
    const timer = setInterval(check, 30_000);
    return () => { controller.abort(); clearInterval(timer); };
  }, []);
  async function signIn(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch("/api/local-auth", { method: "POST", headers: { "Content-Type": "application/json", "X-NetSentinel-Request": "local-ui-v1" }, body: JSON.stringify({ password }) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Sign-in failed.");
      setCSRF(body.csrf); setPassword("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign-in service unavailable."); }
    finally { setBusy(false); }
  }
  async function signOut() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/local-auth", { method: "DELETE", headers: { "X-NetSentinel-Request": "local-ui-v1", "X-CSRF-Token": csrf ?? "" } });
      if (!response.ok) throw new Error("Sign-out failed. Close this tab and restart the local server to revoke sessions.");
      setCSRF(null);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign-out unavailable."); }
    finally { setBusy(false); }
  }
  if (checking) return <main className="local-login"><p role="status">Checking local access…</p></main>;
  if (csrf) return <><div className="local-access-bar"><span>{lab ? "Private AI experiment lab" : "Private research monitor"} · session expires after 4 hours</span><button onClick={signOut} disabled={busy}>Sign out</button>{error && <span role="alert">{error}</span>}</div>{render ? render(csrf) : <Dashboard />}</>;
  return <main className="local-login"><div className="panel"><p className="eyebrow">On this computer</p><h1>{lab ? "Open your AI experiment lab" : "Open your local monitor"}</h1><p>Sign in with the operator password configured during local setup. {lab ? "Train and evaluate models on clearly labelled generated traffic; no packets are sent." : "Network observations stay in your local research system."}</p><form onSubmit={signIn}><label htmlFor="operator-password">Local operator password</label><input id="operator-password" type="password" autoComplete="current-password" required maxLength={256} value={password} onChange={(event) => setPassword(event.target.value)} /><button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form>{error && <p role="alert">{error}</p>}<p>No password configured yet? Follow <code>docs/LOCAL_AUTH.md</code> in the installed project. This page does not control Windows security; use the separately installed companion for that.</p></div></main>;
}
