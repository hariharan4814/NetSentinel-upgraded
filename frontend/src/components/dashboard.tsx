"use client";
import { useState, useEffect, type FormEvent, type ReactNode } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  MODES,
  UUID,
  currentRate,
  formatRate,
  isFresh,
  utc,
  statusFreshness,
  ANOMALY_DISCLAIMER,
  type CaptureStatus,
  type Session,
  type Mode,
  type Sample,
  type Selection,
  type Window,
  type AnomalyResult,
} from "@/lib/contracts";
import { useMonitor } from "@/lib/use-monitor";

// Hook to check backend health even when no session is selected
function useGlobalHealth(activeHealthData?: boolean, activeLoaded?: boolean) {
  const [reachable, setReachable] = useState<boolean | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (activeLoaded) {
      return;
    }

    let disposed = false;
    async function check() {
      try {
        const res = await fetch("/api/backend/health", { cache: "no-store" });
        if (!res.ok) throw new Error("Health check failed");
        const json = await res.json();
        if (!disposed) {
          setReachable(json.status === "ok" && json.database === "reachable");
          setChecked(true);
        }
      } catch {
        if (!disposed) {
          setReachable(false);
          setChecked(true);
        }
      }
    }

    void check();
    const interval = setInterval(check, 10000);
    return () => {
      disposed = true;
      clearInterval(interval);
    };
  }, [activeLoaded]);

  const isReachable = activeLoaded ? activeHealthData : reachable;
  const isChecked = activeLoaded ? true : checked;

  return { reachable: isReachable, checked: isChecked };
}

// Active Section Tracker (ScrollSpy)
const NAV_SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "anomaly", label: "Anomaly Detection" },
  { id: "telemetry", label: "Live Telemetry" },
  { id: "windows", label: "Traffic Windows" },
  { id: "capture", label: "Capture & Interface" },
  { id: "session", label: "Session Summary" },
];

function useScrollSpy(sectionIds: string[]) {
  const [activeId, setActiveId] = useState<string>("overview");

  useEffect(() => {
    function handleScroll() {
      const scrollPosition = window.scrollY + 120;
      for (let i = sectionIds.length - 1; i >= 0; i--) {
        const el = document.getElementById(sectionIds[i]);
        if (el) {
          const top = el.offsetTop;
          if (scrollPosition >= top) {
            setActiveId(sectionIds[i]);
            return;
          }
        }
      }
      setActiveId(sectionIds[0]);
    }

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, [sectionIds]);

  return activeId;
}

// Header Component
function Header({
  activeMode,
  backendReachable,
  backendChecked,
}: {
  activeMode: Mode;
  backendReachable: boolean | undefined | null;
  backendChecked: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeSection = useScrollSpy(NAV_SECTIONS.map((s) => s.id));
  const shouldReduceMotion = useReducedMotion();

  function scrollTo(id: string) {
    setMobileOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: shouldReduceMotion ? "auto" : "smooth" });
    }
  }

  return (
    <header className="top-nav" role="banner">
      <div className="top-nav-inner">
        <a
          className="brand"
          href="#overview"
          onClick={(e) => {
            e.preventDefault();
            scrollTo("overview");
          }}
          aria-label="NetSentinel Home"
        >
          <span className="brand-mark">N</span>
          <span className="brand-name">NetSentinel</span>
          <span className="brand-badge">Local</span>
        </a>

        <nav className="desktop-nav" aria-label="Main Navigation">
          {NAV_SECTIONS.map((sec) => {
            const isActive = activeSection === sec.id;
            return (
              <a
                key={sec.id}
                href={`#${sec.id}`}
                className={`nav-link ${isActive ? "active" : ""}`}
                onClick={(e) => {
                  e.preventDefault();
                  scrollTo(sec.id);
                }}
              >
                {sec.label}
                {isActive && !shouldReduceMotion && (
                  <motion.span
                    className="nav-active-pill"
                    layoutId="active-pill"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </a>
            );
          })}
        </nav>

        <div className="nav-controls">
          <span className={`badge mode-${activeMode.toLowerCase()}`} title="Current Provenance Mode">
            {activeMode}
          </span>

          <div
            className={`status-indicator ${
              !backendChecked ? "connecting" : backendReachable ? "online" : "offline"
            }`}
            title="Backend Connectivity Status"
          >
            <span className="status-dot" />
            <span className="status-text">
              {!backendChecked
                ? "Connecting…"
                : backendReachable
                ? "Backend reachable"
                : "Backend unavailable"}
            </span>
          </div>

          <button
            type="button"
            className="mobile-toggle"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
          >
            <span className={`hamburger-icon ${mobileOpen ? "open" : ""}`}>
              <span />
              <span />
              <span />
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.nav
            className="mobile-nav"
            aria-label="Mobile Navigation"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
          >
            {NAV_SECTIONS.map((sec) => (
              <a
                key={sec.id}
                href={`#${sec.id}`}
                className={`mobile-nav-link ${activeSection === sec.id ? "active" : ""}`}
                onClick={(e) => {
                  e.preventDefault();
                  scrollTo(sec.id);
                }}
              >
                {sec.label}
              </a>
            ))}
            <div className="mobile-nav-status">
              <span className={`badge mode-${activeMode.toLowerCase()}`}>{activeMode}</span>
              <span className="mobile-status-text">
                {!backendChecked
                  ? "Connecting to backend…"
                  : backendReachable
                  ? "Backend reachable"
                  : "Backend unavailable"}
              </span>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}

// Footer Component
function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="app-footer" role="contentinfo">
      <div className="footer-content">
        <div className="footer-brand">
          <div className="footer-logo">
            <span className="brand-mark footer-mark">N</span>
            <strong>NetSentinel</strong>
          </div>
          <p className="footer-subtitle">Intelligent Network Monitoring &amp; Anomaly Detection</p>
          <p className="footer-observation">Own-host observation · Local capture telemetry</p>
        </div>

        <div className="footer-meta">
          <p className="footer-stack">
            Next.js · Django · PostgreSQL · Isolation Forest
          </p>
          <p className="footer-disclaimer">
            Anomalies indicate statistical deviation, not confirmed malicious activity.
          </p>
          <div className="footer-bottom">
            <span>© {currentYear} NetSentinel. All rights reserved.</span>
            <span>All timestamps shown in UTC · Missing observations never become zero</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

function Panel({ id, title, detail, children }: { id?: string; title: string; detail?: string; children: ReactNode }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.section
      id={id}
      className="panel"
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.25 }}
      whileHover={shouldReduceMotion ? undefined : { y: -2 }}
    >
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {detail && <p>{detail}</p>}
        </div>
      </div>
      {children}
    </motion.section>
  );
}

function Notice({ children, error = false, className = "" }: { children: ReactNode; error?: boolean; className?: string }) {
  return (
    <p className={`notice ${error ? "error" : ""} ${className}`} role={error ? "alert" : undefined}>
      {children}
    </p>
  );
}

function RefreshError({ error, retained }: { error: string; retained: boolean }) {
  return (
    <Notice error>
      Refresh failed: {error} {retained ? "Showing stale historical data from the last successful load; current state is unavailable." : "No previously loaded data is available."}
    </Notice>
  );
}

function Metric({ title, value, detail }: { title: string; value: string; detail: string }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.section
      className="metric"
      whileHover={shouldReduceMotion ? undefined : { y: -2 }}
      transition={{ duration: 0.15 }}
    >
      <p>{title}</p>
      <strong>{value}</strong>
      <small>{detail}</small>
    </motion.section>
  );
}

function CopyButton({ text, label = "Copy ID" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  function handleCopy() {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      void navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <motion.button
      type="button"
      className={`copy-btn ${copied ? "copied" : ""}`}
      onClick={handleCopy}
      title={`Copy ${text}`}
      aria-label={copied ? "Copied!" : label}
      whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
    >
      {copied ? "Copied!" : label}
    </motion.button>
  );
}

export function Dashboard() {
  const [selection, setSelection] = useState<Selection | null>(null);
  const [session, setSession] = useState("");
  const [mode, setMode] = useState<Mode>("LIVE");
  const [error, setError] = useState("");
  const shouldReduceMotion = useReducedMotion();

  const currentMode = selection?.mode ?? mode;
  const globalHealth = useGlobalHealth();

  function connect(event: FormEvent) {
    event.preventDefault();
    if (!UUID.test(session.trim())) {
      setError("Enter a valid monitoring session UUID.");
      return;
    }
    setError("");
    setSelection({ session: session.trim().toLowerCase(), mode });
  }

  const fadeInUp = {
    initial: { opacity: 0, y: shouldReduceMotion ? 0 : 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: shouldReduceMotion ? 0 : -8 },
    transition: { duration: shouldReduceMotion ? 0 : 0.25, ease: "easeOut" as const },
  };

  return (
    <div className="shell">
      <Header
        activeMode={currentMode}
        backendReachable={globalHealth.reachable}
        backendChecked={globalHealth.checked}
      />

      <main id="overview" className="main-content">
        <header className="page-heading">
          <div>
            <p className="eyebrow">NETWORK MONITOR &amp; ANOMALY EXPLAINABILITY</p>
            <h1>Your network, observed.</h1>
            <p>Measured traffic. Calibrated statistical baselines. One session at a time.</p>
          </div>
          <span className="pill">Local dashboard</span>
        </header>

        <form className="selector" onSubmit={connect}>
          <div className="session-input">
            <label htmlFor="session-id">Monitoring session UUID</label>
            <input
              id="session-id"
              value={session}
              onChange={(e) => setSession(e.target.value)}
              placeholder="Paste an existing session UUID"
              spellCheck={false}
              autoComplete="off"
              required
              aria-describedby="selection-help"
            />
          </div>
          <div>
            <label htmlFor="mode">Provenance</label>
            <select id="mode" value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
              {MODES.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <motion.button
            type="submit"
            whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
          >
            View session <span aria-hidden="true">→</span>
          </motion.button>
        </form>
        <p id="selection-help" className="help">
          Use the UUID returned by session registration. Selecting a mode does not start capture or generate traffic.
        </p>

        {error && <Notice error>{error}</Notice>}

        <AnimatePresence mode="wait">
          {selection ? (
            <motion.div key={`${selection.session}:${selection.mode}`} {...fadeInUp}>
              <Monitor selection={selection} />
            </motion.div>
          ) : (
            <motion.div key="empty" {...fadeInUp}>
              <Panel title="Choose a session to begin" detail="Your data stays local.">
                <div className="empty">
                  <span className="empty-symbol" aria-hidden="true">⌁</span>
                  <h3>Ready when your data is.</h3>
                  <p>Enter a session UUID and its mode to read recent telemetry, traffic windows, and anomaly explanations.</p>
                  <p>The API does not currently provide a session browser.</p>
                </div>
              </Panel>
              <div className="two-column">
                <CapturePanel />
                <Panel id="session" title="Session summary">
                  <Notice>No session selected.</Notice>
                </Panel>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}

function AnomalySection({
  anomalies,
  loaded,
  error,
}: {
  anomalies: AnomalyResult[];
  loaded: boolean;
  error?: string;
}) {
  const latest = anomalies[0];
  const isAnomalous = latest?.label === "ANOMALOUS";
  const shouldReduceMotion = useReducedMotion();

  return (
    <Panel
      id="anomaly"
      title="Anomaly Detection"
      detail="Isolation Forest scoring · calibrated threshold · feature-level explainability"
    >
      {error && <RefreshError error={error} retained={!!anomalies.length} />}
      {!loaded ? (
        <div className="skeleton-loader">
          <Notice>Loading anomaly results…</Notice>
        </div>
      ) : !anomalies.length ? (
        !error && (
          <Notice>
            No recent anomaly results for this session and mode. Observations may still be in the scoring pipeline or older than 24 hours.
          </Notice>
        )
      ) : (
        <>
          <motion.div
            className="anomaly-hero"
            initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.25 }}
          >
            <div className={`anomaly-status-card ${isAnomalous ? "status-anomalous" : "status-normal"}`}>
              <motion.span
                className={`badge ${isAnomalous ? "anomalous" : "normal"}`}
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                {latest.label}
              </motion.span>
              <div className="anomaly-score-display">
                {latest.anomaly_score.toFixed(4)}
                <small>
                  Score · {latest.threshold != null ? `Threshold ${latest.threshold.toFixed(4)} · ` : ""}higher = more unusual
                </small>
              </div>
              <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                Scored: {utc(latest.scored_at)}
              </div>
            </div>

            <div className="anomaly-details-card">
              <div>
                <p className="eyebrow" style={{ margin: "0 0 6px" }}>
                  EVIDENCE-BASED EXPLANATION
                </p>
                <div className="anomaly-explanation">
                  <strong>{latest.explanation}</strong>
                </div>
                {latest.deviating_features && latest.deviating_features.length > 0 && (
                  <div className="deviating-tags">
                    {latest.deviating_features.map((feat) => (
                      <span key={feat} className="deviating-tag">
                        {feat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="score-bar-container">
                <div className="score-bar-labels">
                  <span>Model: <span className="identifier">{latest.model_version_id.slice(0, 8)}…</span><CopyButton text={latest.model_version_id} /></span>
                  {latest.threshold != null && (
                    <span>Threshold: <strong>{latest.threshold.toFixed(4)}</strong></span>
                  )}
                  <span>Window: <span className="identifier">{latest.window_id.slice(0, 8)}…</span><CopyButton text={latest.window_id} /></span>
                </div>
              </div>
            </div>
          </motion.div>

          <Notice className="disclaimer">
            {ANOMALY_DISCLAIMER}
          </Notice>

          <details>
            <summary>Inspect recent anomaly scoring history ({anomalies.length} records)</summary>
            <div className="table-scroll">
              <table>
                <caption>Recent scored ten-second windows and descriptive feature explanations.</caption>
                <thead>
                  <tr>
                    <th>Observed (UTC)</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Threshold</th>
                    <th>Explanation</th>
                    <th>Window ID</th>
                  </tr>
                </thead>
                <tbody>
                  {anomalies.map((res) => (
                    <tr key={res.id} className={res.label === "ANOMALOUS" ? "anomalous-row" : ""}>
                      <td>{utc(res.observed_at)}</td>
                      <td>
                        <span className={`badge ${res.label === "ANOMALOUS" ? "anomalous" : "normal"}`}>
                          {res.label}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{res.anomaly_score.toFixed(4)}</td>
                      <td>{res.threshold != null ? res.threshold.toFixed(4) : "—"}</td>
                      <td>{res.explanation}</td>
                      <td>
                        <span className="identifier">{res.window_id.slice(0, 8)}…</span>
                        <CopyButton text={res.window_id} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </Panel>
  );
}

function CapturePanel({
  interfaceName,
  status,
  loaded = true,
  error,
  now = 0,
  paused = false,
}: {
  interfaceName?: string;
  status?: CaptureStatus;
  loaded?: boolean;
  error?: string;
  now?: number;
  paused?: boolean;
}) {
  return (
    <Panel
      id="capture"
      title="Capture & interface"
      detail="Latest reported capture event; not a physical interface link check."
    >
      {error ? (
        <RefreshError error={error} retained={!!status} />
      ) : !loaded ? (
        <div className="skeleton-loader">
          <Notice>Loading capture status...</Notice>
        </div>
      ) : !status ? (
        <Notice>
          No recent capture status for this session and mode. Current state and gap information are unavailable.
        </Notice>
      ) : (
        <Notice>{paused ? "Polling paused - current state unavailable" : statusFreshness(status, now)}</Notice>
      )}
      <dl>
        <div>
          <dt>Interface name</dt>
          <dd>{interfaceName ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Latest reported capture state</dt>
          <dd>{status?.state ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Status validity</dt>
          <dd>{status ? (status.valid ? "Valid" : "Invalid") : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Observed (UTC)</dt>
          <dd>{status ? utc(status.observed_at) : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Mode</dt>
          <dd>{status?.mode ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Interface link state</dt>
          <dd>Unavailable</dd>
        </div>
        <div>
          <dt>Recorded monitoring gap</dt>
          <dd>{status ? `${status.monitoring_gap_seconds} s` : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Recovery attempts</dt>
          <dd>{status?.recovery_attempts ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Loss started (UTC)</dt>
          <dd>{status?.loss_started_at ? utc(status.loss_started_at) : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Gap ended (UTC)</dt>
          <dd>{status?.gap_ended_at ? utc(status.gap_ended_at) : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Reason</dt>
          <dd>{status?.reason ?? "Unavailable"}</dd>
        </div>
      </dl>
      <p className="notice">
        Gap duration is the stored event value, not a running timer or traffic measurement. Missing observations never become zero traffic.
      </p>
    </Panel>
  );
}

function SessionPanel({
  session,
  selection,
  loaded,
  error,
}: {
  session?: Session;
  selection: Selection;
  loaded: boolean;
  error?: string;
}) {
  return (
    <Panel id="session" title="Session summary" detail="Stored monitoring-session metadata.">
      {error ? (
        <RefreshError error={error} retained={!!session} />
      ) : !loaded ? (
        <div className="skeleton-loader">
          <Notice>Loading session metadata...</Notice>
        </div>
      ) : !session ? (
        <Notice>Session metadata unavailable.</Notice>
      ) : null}
      <dl>
        <div>
          <dt>Interface name</dt>
          <dd>{session?.interface_name ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Mode (selected)</dt>
          <dd>{session?.mode ?? selection.mode}</dd>
        </div>
        <div>
          <dt>Session ID (selected)</dt>
          <dd className="identifier">
            {session?.session_id ?? selection.session}
            <CopyButton text={session?.session_id ?? selection.session} />
          </dd>
        </div>
        <div>
          <dt>Run ID</dt>
          <dd className="identifier">
            {session?.run_id ?? "Unavailable"}
            {session?.run_id && <CopyButton text={session.run_id} />}
          </dd>
        </div>
        <div>
          <dt>Source ID</dt>
          <dd className="identifier">
            {session?.source_id ?? "Unavailable"}
            {session?.source_id && <CopyButton text={session.source_id} />}
          </dd>
        </div>
        <div>
          <dt>Started (UTC)</dt>
          <dd>{session ? utc(session.started_at) : "Unavailable"}</dd>
        </div>
        <div>
          <dt>Observation profile</dt>
          <dd>{session?.observation_profile ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Schema version</dt>
          <dd>{session?.schema_version ?? "Unavailable"}</dd>
        </div>
      </dl>
      <p className="notice">
        LIVE labels provenance, not freshness. Polls never start the sensor. No automatic sensor uploader is installed.
      </p>
    </Panel>
  );
}

function Monitor({ selection }: { selection: Selection }) {
  const snapshot = useMonitor(selection);
  const samples = snapshot.telemetry.data?.results ?? [];
  const windows = snapshot.windows.data?.results ?? [];
  const anomalies = snapshot.anomalies.data?.results ?? [];
  const latest = samples[0];
  const status = snapshot.capture.data?.results[0];
  const identity = snapshot.session.data ?? status ?? latest ?? windows[0] ?? anomalies[0];
  const interrupted =
    !!status && !status.valid && !!latest && Date.parse(status.observed_at) >= Date.parse(latest.observed_at);
  const available = snapshot.health.data === true && !snapshot.telemetry.error && !snapshot.paused && !interrupted;
  const fresh = isFresh(latest, snapshot.now);
  const freshness = !snapshot.loaded
    ? "Loading"
    : snapshot.paused
    ? "Polling paused"
    : !available
    ? "Unavailable"
    : !latest
    ? "No samples"
    : !latest.valid
    ? "Invalid observation"
    : fresh
    ? "Recent observation"
    : "Stale observation";

  return (
    <>
      <div className="status-strip" aria-live="polite">
        <span className={`badge mode-${selection.mode.toLowerCase()}`}>{selection.mode}</span>
        <span>{identity?.interface_name ?? "Interface unavailable"}</span>
        <span className="connection">
          {!snapshot.loaded
            ? "Connecting to backend…"
            : snapshot.health.data
            ? "Backend reachable"
            : "Backend unavailable"}
        </span>
      </div>

      {snapshot.health.error && <Notice error>{snapshot.health.error} Retrying with bounded backoff.</Notice>}

      <div className="metrics">
        <Metric
          title={selection.mode === "LIVE" ? "Current upload" : "Latest upload"}
          value={formatRate(currentRate(latest, "upload", snapshot.now, available))}
          detail="OS counters · bytes per second"
        />
        <Metric
          title={selection.mode === "LIVE" ? "Current download" : "Latest download"}
          value={formatRate(currentRate(latest, "download", snapshot.now, available))}
          detail="OS counters · bytes per second"
        />
        <Metric
          title="Packets sent / received"
          value={
            latest
              ? `${latest.packets_sent.toLocaleString()} / ${latest.packets_received.toLocaleString()}`
              : "Unavailable"
          }
          detail="Latest OS cumulative totals · not session totals"
        />
        <Metric
          title="Observation coverage"
          value={freshness}
          detail={latest ? `Latest: ${utc(latest.observed_at)}` : "No observation timestamp available"}
        />
      </div>

      <AnomalySection
        anomalies={anomalies}
        loaded={snapshot.loaded}
        error={snapshot.anomalies.error}
      />

      <Panel id="telemetry" title="Live telemetry" detail={`Last ${samples.length} returned samples · ${selection.mode} · OS_COUNTERS`}>
        {snapshot.telemetry.error && <RefreshError error={snapshot.telemetry.error} retained={!!samples.length} />}
        {!snapshot.loaded ? (
          <div className="skeleton-loader">
            <Notice>Loading telemetry…</Notice>
          </div>
        ) : !samples.length ? (
          !snapshot.telemetry.error && (
            <Notice>
              No recent telemetry for this session and mode. The database may be empty, the selection may not match, or observations may be older than 24 hours.
            </Notice>
          )
        ) : (
          <>
            {(!fresh || !latest?.valid) && (
              <Notice>
                {latest?.reason ?? "Latest observation is older than the 5-second display freshness limit."} Current rates are unavailable; historical observations remain below.
              </Notice>
            )}
            <TrafficChart samples={samples} />
            <details>
              <summary>Inspect returned samples ({samples.length})</summary>
              <div className="table-scroll">
                <table>
                  <caption>Historical OS-counter observations; invalid rates remain unavailable.</caption>
                  <thead>
                    <tr>
                      <th>Observed (UTC)</th>
                      <th>Upload</th>
                      <th>Download</th>
                      <th>Validity / reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {samples.map((sample) => (
                      <tr key={sample.id}>
                        <td>{utc(sample.observed_at)}</td>
                        <td>{formatRate(sample.valid ? sample.upload_bytes_per_second : null)}</td>
                        <td>{formatRate(sample.valid ? sample.download_bytes_per_second : null)}</td>
                        <td>{sample.valid ? "Valid" : `Invalid · ${sample.reason}`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </>
        )}
      </Panel>

      <Panel id="windows" title="Traffic windows" detail="Ten-second intervals · PACKET_METADATA · IP bytes include IP headers">
        {snapshot.windows.error && <RefreshError error={snapshot.windows.error} retained={!!windows.length} />}
        {!snapshot.loaded ? (
          <div className="skeleton-loader">
            <Notice>Loading windows…</Notice>
          </div>
        ) : !windows.length ? (
          !snapshot.windows.error && (
            <Notice>No recent windows for this session and mode. Missing windows are not zero traffic.</Notice>
          )
        ) : (
          <WindowTable windows={windows} />
        )}
        {snapshot.windows.data?.next && (
          <p className="help">Showing the newest 20 windows. Older records are outside this dashboard page.</p>
        )}
      </Panel>

      <div className="two-column">
        <CapturePanel
          interfaceName={identity?.interface_name}
          status={status}
          loaded={snapshot.loaded}
          error={snapshot.capture.error}
          now={snapshot.now}
          paused={snapshot.paused}
        />
        <SessionPanel
          session={snapshot.session.data}
          selection={selection}
          loaded={snapshot.loaded}
          error={snapshot.session.error}
        />
      </div>
    </>
  );
}

function TrafficChart({ samples }: { samples: Sample[] }) {
  const chronological = [...samples].reverse();
  const first = Date.parse(chronological[0].observed_at),
    last = Date.parse(chronological[chronological.length - 1].observed_at);
  const max = Math.max(
    1,
    ...samples.flatMap((s) => (s.valid ? [s.upload_bytes_per_second ?? 0, s.download_bytes_per_second ?? 0] : []))
  );

  return (
    <div className="chart">
      <div className="chart-legend">
        <span>
          <i className="upload-key" />
          Upload
        </span>
        <span>
          <i className="download-key" />
          Download
        </span>
        <span>{formatRate(max)} scale ceiling</span>
      </div>
      <svg
        viewBox="0 0 800 180"
        role="img"
        aria-label="Historical upload and download observations. Individual points only; missing and invalid observations are not connected or replaced with zeros."
      >
        <line x1="20" y1="155" x2="780" y2="155" className="chart-axis" />
        {chronological.map((s) => {
          const x = 20 + ((Date.parse(s.observed_at) - first) / Math.max(1000, last - first)) * 760;
          if (!s.valid) return <text key={s.id} x={x} y="170" className="invalid-mark">×</text>;
          return (
            <g key={s.id}>
              <circle
                cx={x}
                cy={150 - ((s.upload_bytes_per_second ?? 0) / max) * 130}
                r="3.5"
                className="upload-point"
              />
              <circle
                cx={x}
                cy={150 - ((s.download_bytes_per_second ?? 0) / max) * 130}
                r="2.5"
                className="download-point"
              />
            </g>
          );
        })}
      </svg>
      <div className="chart-times">
        <span>{utc(chronological[0].observed_at)}</span>
        <span>{utc(chronological[chronological.length - 1].observed_at)}</span>
      </div>
      <p className="help">
        Each point is a recorded observation. Missing intervals stay blank; × marks invalid samples. Exact values are in the sample table.
      </p>
    </div>
  );
}

function WindowTable({ windows }: { windows: Window[] }) {
  return (
    <div className="table-scroll">
      <table>
        <caption>Returned aggregate windows. Partial rows are invalid observations, not idle capture.</caption>
        <thead>
          <tr>
            <th>Window start (UTC)</th>
            <th>Coverage</th>
            <th>Packets</th>
            <th>IP bytes</th>
            <th>TCP / UDP</th>
            <th>Flow keys</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {windows.map((window) => (
            <tr key={window.id} className={window.partial ? "partial-row" : ""}>
              <td>{utc(window.start)}</td>
              <td>
                <span className={`badge ${window.valid ? "valid" : "partial"}`}>
                  {window.partial ? "Partial · invalid" : "Complete · valid"}
                </span>
              </td>
              <td>{window.packets.toLocaleString()}</td>
              <td>{window.ip_bytes.toLocaleString()}</td>
              <td>
                {window.tcp_packets.toLocaleString()} / {window.udp_packets.toLocaleString()}
              </td>
              <td>{window.flow_count.toLocaleString()}</td>
              <td>{window.reason ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
