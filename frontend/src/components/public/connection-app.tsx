"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import Link from "next/link";
import { CHECK_VERSION, HISTORY_KEY, MAX_HISTORY, PROBE_COUNT, formatDuration, interpretation, measurementScope, parseHistory, runCheck, summarize, supportReport, transferSeconds, type Check, type Probe, type Scope } from "@/lib/connection-check";
import { issues, type IssueId } from "@/lib/troubleshooting";
import { Icon, type IconName } from "./icon";
import { PublicTools } from "./public-tools";

type View = "overview" | "fix" | "history" | "planner" | "guide" | "speed" | "network" | "reports" | "companion";
const navigation: { id: View; label: string; icon: IconName }[] = [
  { id: "overview", label: "Overview", icon: "grid" },
  { id: "speed", label: "Speed test", icon: "pulse" },
  { id: "network", label: "Network details", icon: "globe" },
  { id: "fix", label: "Fix a problem", icon: "tools" },
  { id: "history", label: "Recent checks", icon: "clock" },
  { id: "planner", label: "Download planner", icon: "download" },
  { id: "reports", label: "PDF reports", icon: "book" },
  { id: "companion", label: "Windows companion", icon: "laptop" },
  { id: "guide", label: "How it works", icon: "book" },
];
const timestamp = (at: string) => new Date(at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
const ms = (value: number | null) => value === null ? "—" : Math.round(value).toLocaleString();

function downloadReport(check: Check) {
  const url = URL.createObjectURL(new Blob([supportReport(check)], { type: "text/plain;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = `netsentinel-check-${check.at.slice(0, 10)}.txt`;
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ConnectionApp() {
  const [view, setView] = useState<View>("overview");
  const [scope, setScope] = useState<Scope>("LOCAL");
  const [history, setHistory] = useState<Check[]>([]);
  const [keepHistory, setKeepHistory] = useState(false);
  const [storageNotice, setStorageNotice] = useState("");
  const [probes, setProbes] = useState<Probe[]>([]);
  const [result, setResult] = useState<Check | null>(null);
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState("");
  const [issueId, setIssueId] = useState<IssueId>("slow");
  const controller = useRef<AbortController | null>(null);
  const main = useRef<HTMLElement | null>(null);
  const stats = summarize(result ? result.probes : probes);
  const advice = result ? interpretation(result) : null;

  useEffect(() => {
    // Client-only initialization avoids reading device data during server rendering.
    const timer = setTimeout(() => {
      setScope(measurementScope(window.location.hostname));
      try {
        const consent = localStorage.getItem(`${HISTORY_KEY}.enabled`) === "true";
        setKeepHistory(consent);
        const saved = consent ? parseHistory(localStorage.getItem(HISTORY_KEY)) : [];
        setHistory(saved);
        if (consent) localStorage.setItem(HISTORY_KEY, JSON.stringify(saved));
        else localStorage.removeItem(HISTORY_KEY);
      } catch { setStorageNotice("Device storage is unavailable. Your check and report will still work."); }
    }, 0);
    function visibility() {
      if (document.hidden && controller.current) {
        controller.current.abort();
        setNotice("Check paused because this tab was hidden. Run a new check while keeping this tab open.");
      }
    }
    document.addEventListener("visibilitychange", visibility);
    return () => { clearTimeout(timer); controller.current?.abort(); document.removeEventListener("visibilitychange", visibility); };
  }, []);

  function navigate(next: View) {
    if (next !== view && controller.current) { controller.current.abort(); setNotice("Check cancelled. You can start again when you’re ready."); }
    setView(next);
    window.scrollTo({ top: 0 });
    requestAnimationFrame(() => main.current?.focus());
  }
  function chooseIssue(id: IssueId) { setIssueId(id); navigate("fix"); }
  function persist(next: Check[]) {
    const bounded = parseHistory(JSON.stringify(next));
    setHistory(bounded);
    try { if (bounded.length) localStorage.setItem(HISTORY_KEY, JSON.stringify(bounded)); else localStorage.removeItem(HISTORY_KEY); }
    catch { setStorageNotice("Couldn’t update device storage. Results remain available in this tab; use your browser’s site-data controls to erase any saved copy."); }
  }
  function toggleHistory(enabled: boolean) {
    setKeepHistory(enabled);
    try {
      localStorage.setItem(`${HISTORY_KEY}.enabled`, String(enabled));
      if (!enabled) { localStorage.removeItem(HISTORY_KEY); setHistory([]); }
    } catch { setStorageNotice("Device storage is unavailable. Use your browser’s site-data controls to remove previously saved checks."); }
  }
  async function start() {
    if (controller.current) return;
    const active = new AbortController(); controller.current = active;
    setRunning(true); setResult(null); setProbes([]); setNotice("");
    try {
      const completed = await runCheck({ signal: active.signal, onProgress: setProbes });
      const check: Check = { id: crypto.randomUUID(), at: new Date().toISOString(), scope: measurementScope(location.hostname), version: CHECK_VERSION, probes: completed };
      setResult(check);
      if (keepHistory) persist([check, ...history].slice(0, MAX_HISTORY));
    } catch {
      setProbes([]);
      if (!active.signal.aborted) setNotice("This browser could not finish the check. Try again in an up-to-date browser.");
    } finally {
      if (controller.current === active) { controller.current = null; setRunning(false); }
    }
  }
  function cancel() { controller.current?.abort(); setNotice("Check cancelled. No partial result was saved."); }

  return <div className="ns-app">
    <a className="ns-skip" href="#main-content">Skip to content</a>
    <aside className="ns-sidebar">
      <Link className="ns-brand" href="/" aria-label="NetSentinel home"><span className="ns-brand-mark"><Icon name="pulse" size={24} /></span><span>NetSentinel<span className="ns-brand-sub">A little clarity. Better connected.</span></span></Link>
      <p className="ns-nav-label">YOUR CONNECTION</p>
      <nav aria-label="Main navigation">{navigation.map(item => <button key={item.id} className={`ns-nav-item ${view === item.id ? "is-active" : ""}`} aria-current={view === item.id ? "page" : undefined} onClick={() => navigate(item.id)}><Icon name={item.icon} /><span>{item.label}</span>{view === item.id && <span className="ns-nav-dot" />}</button>)}</nav>
      <div className="ns-sidebar-bottom"><div className="ns-private-card"><Icon name="shield" size={25} /><h3>Your connection.<br />Your business.</h3><p>No account. No packet capture. Saved results stay in your browser.</p><button onClick={() => navigate("guide")}>Meet the privacy-first approach <Icon name="arrow" size={16} /></button></div><span className="ns-sidebar-footer">Made for everyday internet.</span></div>
    </aside>
    <div className="ns-workspace">
      <header className="ns-topbar"><div><span className="ns-topbar-label">WORKSPACE</span><span className="ns-breadcrumb">{navigation.find(n => n.id === view)?.label}</span></div><div className="ns-topbar-right"><span className="ns-small-lock"><Icon name="shield" size={16} /> Private by design</span><button className="ns-help-button" aria-label="Read how it works" onClick={() => navigate("guide")}>?</button></div></header>
      <main ref={main} id="main-content" className="ns-main" tabIndex={-1}>
        {view === "overview" && <>
          <div className="ns-page-heading"><div><p className="ns-eyebrow">LESS GUESSWORK. MORE CLARITY.</p><h1>Let’s check your connection.</h1><p>A quick check, a clearer picture, and a useful next step.</p></div><span className="ns-label"><Icon name="laptop" size={16} /> This browser</span></div>
          <section className="ns-check-panel ns-glass" aria-labelledby="connection-title">
            <div className="ns-check-copy"><div className="ns-tag"><span className={`ns-status-dot ${result ? "has-result" : ""}`} />{running ? "CHECK IN PROGRESS" : result ? `${result.scope} · CHECK COMPLETE` : "READY WHEN YOU ARE"}</div>
              <h2 id="connection-title">{running ? "A few small requests.\nA clearer picture." : advice ? advice.title : <>Good internet starts<br />with understanding it.</>}</h2>
              <p>{running ? `Checking response ${Math.min(probes.length + 1, PROBE_COUNT)} of ${PROBE_COUNT}. Keep this tab open for an accurate snapshot.` : advice ? advice.detail : "Slow pages? Calls cutting out? See how this site responds, then work through a few simple fixes."}</p>
              <div className="ns-check-actions"><button className="ns-button ns-primary" onClick={running ? cancel : start}>{running ? <Icon name="close" size={18} /> : <Icon name="pulse" size={18} />}{running ? "Cancel check" : result ? "Check again" : "Run connection check"}</button>{result ? <button className="ns-button ns-quiet" onClick={() => downloadReport(result)}><Icon name="download" size={17} />Save report</button> : <span className="ns-action-note">8 small requests · No installation</span>}</div>
              {scope === "LOCAL" && <p className="ns-local-note"><Icon name="info" size={15} /> Local preview checks this app, not your internet.</p>}
              <p className="ns-live-message" role="status">{notice || (running ? `${probes.length} of ${PROBE_COUNT} requests completed` : result ? `Finished ${timestamp(result.at)}` : "HTTP response check · No speed or packet-loss measurement")}</p>
            </div>
            <div className="ns-check-visual" aria-hidden="true"><div className="ns-orbit ns-orbit-one" /><div className="ns-orbit ns-orbit-two" /><span className="ns-orbit-node ns-node-one"><Icon name="globe" /></span><span className="ns-orbit-node ns-node-two"><Icon name="laptop" /></span><div className="ns-check-ring" style={{ "--progress": `${running ? probes.length / PROBE_COUNT * 100 : result ? 100 : 0}%` } as CSSProperties}><div className="ns-check-ring-inner"><Icon name={result ? "check" : "wifi"} size={40} /><strong>{running ? `${probes.length} / 8` : result ? `${stats.success} / 8` : "Ready to check"}</strong><span>{running ? "requests completed" : result ? "requests answered" : "A small check. A useful start."}</span></div></div><span className="ns-visual-caption"><span />{result ? "A snapshot, not a diagnosis" : "Only checks when you ask"}</span></div>
          </section>
          <div className="ns-metrics">
            <Metric icon="pulse" label="Typical response" value={ms(stats.median)} unit="ms" note="Median HTTP time to this site" />
            <Metric icon="clock" label="Response range" value={ms(stats.spread)} unit="ms" note="Slowest minus fastest response" />
            <Metric icon="check" label="Requests answered" value={stats.total ? `${stats.success} / ${stats.total}` : "—"} note={stats.total ? `${stats.failed} failed or timed out` : "Your results will appear after a check"} />
          </div>
          <div className="ns-detail-grid"><ResponseChart probes={result?.probes ?? probes} /><section className="ns-glass ns-next-step"><div className="ns-section-kicker"><span className="ns-icon-box"><Icon name="tools" /></span>YOUR NEXT STEP</div><h2>{result && stats.failed ? "Let’s narrow it down." : "Something still feels off?"}</h2><p>A quick check is just the beginning. Tell us what’s happening and we’ll help you work through it.</p><button className="ns-button ns-outline" onClick={() => navigate("fix")}>Find a fix <Icon name="arrow" size={17} /></button><div className="ns-tip"><Icon name="info" size={16} /><span>Try one change at a time, then check again. It makes improvements easier to spot.</span></div></section></div>
          <section className="ns-quick-fixes"><div className="ns-section-heading"><h2>What’s getting in your way?</h2><span>Start with what you’re noticing</span></div><div className="ns-issue-grid">{issues.map(issue => <button className="ns-issue-card" key={issue.id} onClick={() => chooseIssue(issue.id)}><span className="ns-icon-box"><Icon name={issue.icon} /></span><span><strong>{issue.short}</strong><small>{issue.description}</small></span><Icon name="arrow" size={17} /></button>)}</div></section>
          <div className="ns-privacy-line"><Icon name="shield" size={17} /><span>No browsing history. No network scanning. Just a check you control.</span><button onClick={() => navigate("guide")}>How it works</button></div>
        </>}
        {view === "fix" && <Troubleshooter issueId={issueId} setIssueId={setIssueId} onCheck={() => navigate("overview")} />}
        {view === "history" && <>
          <PageHeading eyebrow="A LITTLE PERSPECTIVE" title="See what changed." description="Compare a check before and after a fix. Times are shown in your device’s time zone." />
          <section className="ns-glass ns-history-settings"><div><h2>Keep recent checks on this device</h2><p>Optional. Up to 10 checks, for 7 days. Turning this off deletes saved checks.</p></div><label className="ns-toggle"><input type="checkbox" checked={keepHistory} disabled={running} onChange={e => toggleHistory(e.target.checked)} /><span>{keepHistory ? "Enabled" : "Disabled"}</span></label></section>
          {storageNotice && <p role="status" className="ns-notice">{storageNotice}</p>}
          {history.length > 1 && <Comparison current={history[0]} previous={history.find((h, i) => i > 0 && h.scope === history[0].scope)} />}
          <section className="ns-glass ns-history"><div className="ns-section-heading"><h2>Recent checks <span className="ns-count">{history.length}</span></h2>{history.length > 0 && <button className="ns-text-button" onClick={() => persist([])}><Icon name="trash" size={16} />Delete all</button>}</div>{!history.length ? <div className="ns-empty"><Icon name="clock" size={38} /><h3>Your next check is a fresh start.</h3><p>Enable history before checking to keep a result here. You can always download the current result without saving history.</p><button className="ns-button ns-primary" onClick={() => navigate("overview")}>Go to connection check</button></div> : <div className="ns-history-list">{history.map(check => { const summary = summarize(check.probes); return <article key={check.id}><div><span className="ns-tag">{check.scope} · BROWSER CHECK</span><h3>{timestamp(check.at)}</h3><p>{summary.success}/8 answered · {ms(summary.median)} ms typical response</p></div><div className="ns-history-actions"><button className="ns-button ns-outline" onClick={() => downloadReport(check)}><Icon name="download" size={16} />Report</button><button className="ns-icon-button" aria-label={`Delete check from ${timestamp(check.at)}`} onClick={() => persist(history.filter(h => h.id !== check.id))}><Icon name="trash" size={18} /></button></div></article>; })}</div>}</section>
        </>}
        {view === "planner" && <DownloadPlanner />}
        {view === "guide" && <Guide onCheck={() => navigate("overview")} />}
        <PublicTools view={view} checks={result ? [result, ...history.filter(check => check.id !== result.id)] : history} onNavigate={navigate} />
      </main>
      <footer className="ns-footer"><span>NetSentinel <span className="ns-footer-dot">·</span> Make sense of your connection.</span><button onClick={() => navigate("guide")}>About & privacy <Icon name="arrow" size={14} /></button></footer>
    </div>
  </div>;
}

function PageHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="ns-page-heading"><div><p className="ns-eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div></div>;
}
function Metric({ icon, label, value, unit, note }: { icon: IconName; label: string; value: string; unit?: string; note: string }) {
  return <section className="ns-glass ns-metric"><div className="ns-metric-top"><span>{label}</span><Icon name={icon} size={18} /></div><div className="ns-metric-value">{value}{unit && <span>{unit}</span>}</div><p>{note}</p></section>;
}
function ResponseChart({ probes }: { probes: Probe[] }) {
  const peak = Math.max(100, ...probes.map(p => p.ms ?? 0));
  return <section className="ns-glass ns-chart-panel"><div className="ns-section-heading"><h2>Response snapshot</h2><span className="ns-chart-key"><span /> HTTP response</span></div><p>One dot per request. Failed requests stay missing.</p><div className="ns-chart"><div className="ns-chart-scale"><span>{Math.ceil(peak)} ms</span><span>{Math.round(peak / 2)} ms</span><span>0 ms</span></div><div className="ns-chart-plot"><div className="ns-chart-grid" /><div className="ns-chart-points">{Array.from({ length: PROBE_COUNT }, (_, i) => <div className="ns-chart-column" key={i}>{probes[i] && (probes[i].ms === null ? <span className="ns-failed-point" title={`Request ${i + 1} failed`}>×</span> : <span className="ns-chart-point" style={{ bottom: `${Math.max(3, probes[i].ms! / peak * 95)}%` }} title={`Request ${i + 1}: ${probes[i].ms} ms`} />)}<span className="ns-x-label">{i + 1}</span></div>)}</div>{!probes.length && <div className="ns-chart-empty"><Icon name="pulse" size={25} /><span>A clear picture starts with a check.</span><small>Your real responses will appear here.</small></div>}</div></div><details className="ns-readings"><summary>View individual measurements</summary><ol>{probes.length ? probes.map((p, i) => <li key={i}>Request {i + 1}: {p.ms === null ? "failed or timed out" : `${p.ms} ms`}</li>) : <li>No measurements yet.</li>}</ol></details></section>;
}
function Troubleshooter({ issueId, setIssueId, onCheck }: { issueId: IssueId; setIssueId: (id: IssueId) => void; onCheck: () => void }) {
  const [completed, setCompleted] = useState<string[]>([]);
  const issue = issues.find(i => i.id === issueId)!;
  const count = issue.steps.filter((_, i) => completed.includes(`${issue.id}-${i}`)).length;
  return <><PageHeading eyebrow="ONE STEP AT A TIME" title="Let’s find a useful next step." description="Start with your symptom. These steps help narrow things down; they don’t assume a cause." /><div className="ns-symptoms" role="group" aria-label="Choose a problem">{issues.map(i => <button key={i.id} aria-pressed={i.id === issueId} className={i.id === issueId ? "is-selected" : ""} onClick={() => setIssueId(i.id)}><Icon name={i.icon} />{i.short}</button>)}</div><section className="ns-glass ns-guide-card"><div className="ns-section-heading"><div><p className="ns-eyebrow">YOUR TROUBLESHOOTING PLAN</p><h2>{issue.title}</h2></div><span className="ns-label">{count} of 4 tried</span></div><div className="ns-step-list">{issue.steps.map(([title, detail], i) => { const key = `${issue.id}-${i}`; return <label className={`ns-step ${completed.includes(key) ? "is-done" : ""}`} key={key}><input type="checkbox" checked={completed.includes(key)} onChange={e => setCompleted(e.target.checked ? [...completed, key] : completed.filter(c => c !== key))} /><span className="ns-step-number">{String(i + 1).padStart(2, "0")}</span><span><strong>{title}</strong><span>{detail}</span></span></label>; })}</div><div className="ns-checklist-footer"><span>{count === 4 ? "Still happening? Share the symptoms and a check report with support." : "Mark a step once you’ve tried it. Progress stays only while this view is open."}</span><button className="ns-text-button" onClick={() => setCompleted(completed.filter(c => !c.startsWith(issueId)))}>Reset steps</button></div></section><div className="ns-callout"><div><h3>Made a change? See how it feels.</h3><p>Run another check and compare it with your previous result.</p></div><button className="ns-button ns-primary" onClick={onCheck}>Back to connection check</button></div><p className="ns-source">For Windows-specific help, see <a href="https://support.microsoft.com/en-us/windows/experience/connectivity-networking/fix-wi-fi-connection-issues-in-windows" target="_blank" rel="noreferrer">Microsoft’s Wi-Fi troubleshooting guide</a>.</p></>;
}
function Comparison({ current, previous }: { current: Check; previous?: Check }) {
  if (!previous) return null;
  const a = summarize(current.probes), b = summarize(previous.probes);
  const difference = a.median !== null && b.median !== null ? a.median - b.median : null;
  return <section className="ns-callout"><div><p className="ns-eyebrow">LATEST VS PREVIOUS · {current.scope}</p><h2>{difference === null ? "Not enough responses to compare" : Math.abs(difference) < 1 ? "Typical response was about the same" : `Typical response was ${Math.round(Math.abs(difference))} ms ${difference > 0 ? "slower" : "faster"}`}</h2><p>{b.success}/8 → {a.success}/8 requests answered. Short checks vary naturally; this does not prove a fix worked.</p></div></section>;
}
function DownloadPlanner() {
  const [size, setSize] = useState("1"); const [unit, setUnit] = useState<"MB" | "GB">("GB"); const [speed, setSpeed] = useState("50");
  const seconds = transferSeconds(Number(size), unit, Number(speed));
  return <><PageHeading eyebrow="PUT THE WAIT IN PERSPECTIVE" title="How long should that download take?" description="Turn a file size and connection speed into a simple estimate." /><div className="ns-planner-grid"><section className="ns-glass ns-guide-card"><p className="ns-eyebrow">ENTER YOUR OWN NUMBERS</p><h2>A little download math.</h2><label className="ns-field">File size<div className="ns-field-row"><input type="number" min="0.01" max="100000" step="any" value={size} onChange={e => setSize(e.target.value)} aria-label="File size" /><select value={unit} onChange={e => setUnit(e.target.value as "MB" | "GB")} aria-label="File size unit"><option>GB</option><option>MB</option></select></div></label><label className="ns-field">Download speed (Mbps)<input type="number" min="0.01" max="100000" step="any" value={speed} onChange={e => setSpeed(e.target.value)} /></label><p>Use a speed you measured elsewhere, or your plan’s advertised speed. Use the separate Speed test to measure a recent transfer, then enter its download result here.</p><div className="ns-presets"><span>Example file sizes</span><button onClick={() => { setSize("25"); setUnit("MB"); }}>25 MB document</button><button onClick={() => { setSize("5"); setUnit("GB"); }}>5 GB video</button><button onClick={() => { setSize("50"); setUnit("GB"); }}>50 GB game</button></div></section><section className="ns-glass ns-estimate" aria-live="polite"><span className="ns-icon-box"><Icon name="download" size={28} /></span><p className="ns-eyebrow">THEORETICAL MINIMUM</p><h2>{seconds === null ? "Check your numbers" : formatDuration(seconds)}</h2><p>{seconds === null ? "Enter a file size and speed greater than zero, up to 100,000 each." : "Allow extra time for network overhead, busy servers, shared connections and Wi-Fi conditions."}</p><div className="ns-formula"><strong>Why the units matter</strong><p>8 megabits (Mb) = 1 megabyte (MB). A 50 Mbps connection transfers at most 6.25 MB per second before overhead.</p><small>Decimal units: 1 GB = 1,000 MB. This estimate isn’t a measured result.</small></div></section></div></>;
}
function Guide({ onCheck }: { onCheck: () => void }) {
  return <><PageHeading eyebrow="A CLEARER CONNECTION" title="Less technical. More helpful." description="NetSentinel helps you understand a frustrating connection and decide what to try next." /><div className="ns-guide-intro ns-glass"><div><p className="ns-eyebrow">THE PROBLEM WE’RE SOLVING</p><h2>“My internet isn’t working.”<br />Now what?</h2><p>A wall of technical numbers rarely tells you what to do. NetSentinel gives you a small, honest connection check, an understandable result and practical steps to narrow down the problem.</p><button className="ns-button ns-primary" onClick={onCheck}>Try a connection check</button></div><div className="ns-how-steps">{[["Check", "Run eight small requests from this browser to this website."], ["Understand", "See which requests answered and how their response times varied."], ["Try one thing", "Follow a relevant troubleshooting step, then compare another check."]].map(([title, body], i) => <div key={title}><span>{i + 1}</span><div><h3>{title}</h3><p>{body}</p></div></div>)}</div></div><section className="ns-glass ns-guide-card"><h2>A few things worth understanding.</h2><div className="ns-faq"><details open><summary>What does the connection check actually measure?</summary><p>It makes eight sequential HTTP requests to a tiny file on this site. Each request has a 3-second timeout. The typical response is the median time; the range is the slowest minus the fastest successful response. These times include browser, connection and server overhead. The check is usually quick, but can take about 28 seconds if requests time out.</p><p>Our advisory thresholds are 300 ms for the median and 150 ms for the range. They are simple comparison prompts, not scientifically validated quality guarantees. Request failures are not packet loss.</p></details><details><summary>How is this check different from the speed test?</summary><p>The lightweight check measures small HTTP responses. The separate Speed test uses explicit transfers to Cloudflare and reports throughput, HTTP latency and jitter. Neither tool measures Wi-Fi signal, ICMP ping, ISP uptime or whether a network is secure. A browser cannot capture packets or see all your devices. It also cannot identify the cause of an outage. On a local or IP-address preview, the result is labelled LOCAL and is not treated as an internet measurement.</p></details><details><summary>Where does my information go?</summary><p>Lightweight check requests go only to this site. The separate speed test contacts Cloudflare only when you start it, and the optional network lookup contacts ipwho.is only after your consent. These providers receive your public IP under their privacy policies. Like other websites, the hosting provider receives ordinary connection information such as your IP address and may retain access logs under its policies. The app has no analytics, accounts, advertising or packet capture. Troubleshooting answers stay in this tab.</p><p>History is off by default. If you enable it, up to 10 checks are kept in this browser for 7 days, with expired entries removed when the app next loads or history changes. You can delete one or all checks, or disable history to erase it. Anyone using this browser profile can see saved checks. Speed history is separately opt-in, capped at 30 tests for 30 days, and contains no IP or location. Current network details stay in this tab only. PDF reports hide addresses and location by default. Downloaded reports remain on your device until you delete them.</p></details><details><summary>Why can a check look fine while a call is still bad?</summary><p>Your call and this website use different servers and may follow different network paths. Eight successful requests are a short snapshot, not a guarantee. Use the video-call troubleshooting steps and note when the problem happens.</p></details><details><summary>Does it keep monitoring in the background?</summary><p>No. Checks start only when you press the button. Leaving the check screen or hiding the tab cancels an active check, and cancelled results are not saved. Keep this tab visible, then repeat a check when a problem occurs. Without internet, an already open page can still show guidance, but loading the site again may fail.</p></details></div></section><div className="ns-callout"><Icon name="shield" size={28} /><div><h3>You stay in control.</h3><p>This public website never changes your router, scans your network, installs a driver or blocks traffic. The separately installed Windows companion provides explicit local controls; it never receives instructions from this public site.</p></div></div></>;
}
