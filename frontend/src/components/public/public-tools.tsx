"use client";

import { useEffect, useRef, useState } from "react";
import type { Check } from "@/lib/connection-check";
import { lookupNetwork, parseSpeedHistory, runSpeedTest, SPEED_HISTORY_KEY, type NetworkDetails, type SpeedProgress, type SpeedResult } from "@/lib/public-measurements";
import { Icon } from "./icon";

const value = (n: number | null, digits = 1) => n === null ? "Unavailable" : n.toLocaleString(undefined, { maximumFractionDigits: digits });
const mb = (n: number | null) => n === null ? "unavailable" : `${value(n / 1e6, 3)} MB`;
const date = (at: string) => new Date(at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
const unique = <T extends { id: string }>(data: T[]) => data.filter((item, i) => data.findIndex(x => x.id === item.id) === i);

export function PublicTools({ view, checks, onNavigate }: { view: string; checks: Check[]; onNavigate: (view: "reports") => void }) {
  const [speedConsent, setSpeedConsent] = useState(false);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<SpeedProgress | null>(null);
  const [result, setResult] = useState<SpeedResult | null>(null);
  const [history, setHistory] = useState<SpeedResult[]>([]);
  const [keep, setKeep] = useState(false);
  const [notice, setNotice] = useState("");
  const [cooldown, setCooldown] = useState(false);
  const [networkConsent, setNetworkConsent] = useState(false);
  const [network, setNetwork] = useState<NetworkDetails | null>(null);
  const [networkBusy, setNetworkBusy] = useState(false);
  const [networkNotice, setNetworkNotice] = useState("");
  const [lookupCooldown, setLookupCooldown] = useState(false);
  const speedController = useRef<AbortController | null>(null);
  const networkController = useRef<AbortController | null>(null);
  const consentRef = useRef(false);
  const [release, setRelease] = useState<{ url: string; version: string } | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      try { const enabled = localStorage.getItem(`${SPEED_HISTORY_KEY}.enabled`) === "true"; setKeep(enabled); consentRef.current = enabled;
        const saved = enabled ? parseSpeedHistory(localStorage.getItem(SPEED_HISTORY_KEY)) : []; setHistory(saved);
        if (enabled) localStorage.setItem(SPEED_HISTORY_KEY, JSON.stringify(saved)); else localStorage.removeItem(SPEED_HISTORY_KEY);
      } catch { setNotice("Browser storage is unavailable. You can still run tests and download reports."); }
    }, 0);
    const hide = () => { if (document.hidden) { speedController.current?.abort(); networkController.current?.abort(); } };
    document.addEventListener("visibilitychange", hide);
    return () => { clearTimeout(timer); speedController.current?.abort(); networkController.current?.abort(); document.removeEventListener("visibilitychange", hide); };
  }, []);
  useEffect(() => { if (view !== "speed") speedController.current?.abort(); if (view !== "network") networkController.current?.abort(); }, [view]);
  useEffect(() => { if (!cooldown) return; const timer = setTimeout(() => setCooldown(false), 60_000); return () => clearTimeout(timer); }, [cooldown]);
  useEffect(() => { if (!lookupCooldown) return; const timer = setTimeout(() => setLookupCooldown(false), 60_000); return () => clearTimeout(timer); }, [lookupCooldown]);
  useEffect(() => {
    if (view !== "companion") return;
    const controller = new AbortController();
    fetch("/companion-release.json", { signal: controller.signal, cache: "no-store", credentials: "omit", redirect: "error" }).then(r => r.ok ? r.json() : null).then(data => {
      if (data?.available === true && typeof data.url === "string" && /^https:\/\/github\.com\/hariharan4814\/NetSentinel-upgraded\/releases\/download\/[^/?#]+\/NetSentinel-Companion-[\d.]+\.zip$/.test(data.url) && typeof data.version === "string" && /^[\d.]{1,20}$/.test(data.version)) setRelease({ url: data.url, version: data.version });
    }).catch(() => {});
    return () => controller.abort();
  }, [view]);

  function persistSpeed(items: SpeedResult[]) {
    const safe = parseSpeedHistory(JSON.stringify(items)); setHistory(safe);
    try { localStorage.setItem(SPEED_HISTORY_KEY, JSON.stringify(safe)); }
    catch { setNotice("Could not save history. Current results remain in this tab. Browser site-data controls can remove an older saved copy."); }
  }
  function toggleKeep(enabled: boolean) {
    consentRef.current = enabled; setKeep(enabled);
    try { localStorage.setItem(`${SPEED_HISTORY_KEY}.enabled`, String(enabled)); if (!enabled) { localStorage.removeItem(SPEED_HISTORY_KEY); setHistory([]); } }
    catch { setNotice("Could not update browser storage. Use browser site-data controls to delete any previously stored tests."); }
  }
  async function startSpeed() {
    if (!speedConsent || speedController.current || cooldown) return;
    const controller = new AbortController(); speedController.current = controller; setRunning(true); setResult(null); setNotice(""); setProgress({ stage: "Preparing", completedSamples: 0, receivedBodyBytes: null, confirmedUploadBytes: 0 });
    try {
      const measured = await runSpeedTest({ signal: controller.signal, onProgress: setProgress });
      setResult(measured);
      if (measured.status === "complete" && consentRef.current) persistSpeed([measured, ...history]);
      if (measured.status !== "complete") setNotice(`${measured.status === "timed-out" ? "Time limit reached" : measured.status === "cancelled" ? "Test cancelled" : "Test could not finish"}. Completed observations are shown below; partial transfers may add uncounted data. This result is not saved to history.`);
    } catch { setNotice(controller.signal.aborted ? "Test cancelled before measurement began." : "Speed testing is unavailable in this browser or on this network. The lightweight connection check still works."); }
    finally { speedController.current = null; setRunning(false); setCooldown(true); }
  }
  async function startLookup() {
    if (!networkConsent || networkController.current || lookupCooldown) return;
    const controller = new AbortController(); networkController.current = controller; setNetworkBusy(true); setNetworkNotice(""); setNetwork(null);
    try { setNetwork(await lookupNetwork(controller.signal)); }
    catch (error) { setNetworkNotice(controller.signal.aborted ? "Lookup cancelled." : error instanceof Error ? error.message : "Lookup unavailable."); }
    finally { networkController.current = null; setNetworkBusy(false); setLookupCooldown(true); }
  }
  const speeds = unique(result ? [result, ...history] : history);
  const previous = result ? history.find(s => s.id !== result.id) : history[1];
  const current = result ?? history[0];
  return <>
    {view === "speed" && <>
      <Heading eyebrow="MEASURE. COMPARE. UNDERSTAND." title="How fast is this connection?" description="A short transfer test to Cloudflare’s edge network. Separate from the lightweight check to this website." />
      <section className="ns-glass ns-tool-panel">
        <div className="ns-section-kicker"><Icon name="pulse" /> BROWSER · USER-STARTED · LIVE MEASUREMENT</div>
        <h2>{running ? `${progress?.stage ?? "Preparing"} in progress` : result ? "Your connection snapshot" : "A speed test you control."}</h2>
        <p>Usually up to <strong>15.5 MB</strong> of test payloads, at most <strong>45 seconds</strong>. Service-limit retries can raise attempted payloads to 62 MB; network overhead is additional. Avoid metered connections if this is too much data.</p>
        <label className="ns-consent"><input type="checkbox" checked={speedConsent} disabled={running} onChange={e => setSpeedConsent(e.target.checked)} /><span>Use Cloudflare’s test service. It receives my public IP and connection requests under its <a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noreferrer">privacy policy</a>. NetSentinel disables the engine’s result logging.</span></label>
        <div className="ns-tool-actions"><button className="ns-button ns-primary" disabled={!running && (!speedConsent || cooldown)} onClick={running ? () => speedController.current?.abort() : startSpeed}><Icon name={running ? "close" : "play"} />{running ? "Cancel speed test" : cooldown ? "Wait one minute to retest" : "Start speed test"}</button>{result && <button className="ns-button ns-outline" onClick={() => onNavigate("reports")}><Icon name="download" />Download PDF report</button>}</div>
        {running && <div className="ns-stage-list" aria-label="Actual test stage">{["Latency", "Download", "Upload"].map(stage => <span key={stage} className={progress?.stage === stage ? "is-current" : ""}>{stage}</span>)}<p>{progress?.completedSamples ?? 0} completed samples. Received: {mb(progress?.receivedBodyBytes ?? null)}. Confirmed upload: {mb(progress?.confirmedUploadBytes ?? 0)}.</p></div>}
        <p className="ns-tool-status" role="status">{notice || (result ? `Finished ${date(result.at)} · ${result.status}` : "No requests leave your browser until you start. Keep this tab visible.")}</p>
      </section>
      <div className="ns-speed-metrics">{[["Download", result?.downloadMbps ?? null, "Mbps"], ["Upload", result?.uploadMbps ?? null, "Mbps"], ["HTTP latency", result?.latencyMs ?? null, "ms"], ["Jitter", result?.jitterMs ?? null, "ms"]].map(([label, n, unit]) => <section className="ns-glass ns-metric" key={String(label)}><div className="ns-metric-top">{label}</div><div className="ns-speed-value">{value(n as number | null)} <small>{unit}</small></div></section>)}</div>
      {result && <section className="ns-glass ns-tool-panel"><h2>Data used by completed observations</h2><p>Received response bodies: <strong>{mb(result.receivedBodyBytes)}</strong>. Confirmed uploaded payloads: <strong>{mb(result.confirmedUploadBytes)}</strong>.</p><p>{result.accountingIncomplete ? "Accounting is incomplete: these values are lower bounds where available." : "These are completed payload counts, not total network or billable bytes."} Aborted or failed transfers, protocol overhead and retransmissions may consume additional data.</p>{result.latencySamples.length > 0 && <div className="ns-sample-chart" aria-label="Latency samples in milliseconds">{result.latencySamples.map((sample, i) => <div key={i}><span style={{ height: `${Math.max(4, sample / Math.max(1, ...result.latencySamples) * 85)}px` }} /><strong>{value(sample)} ms</strong><small>Sample {i + 1}</small></div>)}</div>}</section>}
      <section className="ns-glass ns-tool-panel"><h2>Keep a little perspective.</h2><p>Optional: keep up to 30 completed tests for 30 days in this browser. No IP or location is saved. Turning history off deletes saved speed tests.</p><label className="ns-consent"><input type="checkbox" checked={keep} onChange={e => toggleKeep(e.target.checked)} /><span>Keep speed-test history on this device</span></label>
        {current && previous && <p className="ns-comparison-note">Compared with {date(previous.at)}: download {delta(current.downloadMbps, previous.downloadMbps)} Mbps; upload {delta(current.uploadMbps, previous.uploadMbps)} Mbps. Different network conditions affect comparisons.</p>}
        {history.length > 0 ? <><button className="ns-text-button" onClick={() => persistSpeed([])}>Delete speed history</button><div className="ns-table-wrap"><table className="ns-public-table"><caption>Completed speed tests · times in your device’s time zone</caption><thead><tr><th>When</th><th>Download</th><th>Upload</th><th>Latency</th><th>Action</th></tr></thead><tbody>{history.map(s => <tr key={s.id}><td>{date(s.at)}</td><td>{value(s.downloadMbps)} Mbps</td><td>{value(s.uploadMbps)} Mbps</td><td>{value(s.latencyMs)} ms</td><td><button className="ns-text-button" aria-label={`Delete speed test from ${date(s.at)}`} onClick={() => persistSpeed(history.filter(item => item.id !== s.id))}>Delete</button></td></tr>)}</tbody></table></div></> : <p>No saved speed tests yet.</p>}
      </section>
      <details className="ns-glass ns-tool-panel"><summary>What these numbers mean</summary><p>Throughput is completed payload bits divided by measured transfer time, in decimal Mbps. Download body lengths must match browser Resource Timing before they are used. Upload counts completed request payloads. Timing follows the Cloudflare engine, including its server-time correction.</p><p>Latency is the median of up to six HTTP timing samples. Jitter is the mean absolute difference between successive samples: sum of |next − previous| divided by the number of differences. Missing samples are not zeros.</p><p>A short, single-connection transfer is a snapshot to one provider. It can understate a fast line and includes browser and endpoint limitations. It does not measure packet loss, Wi-Fi signal, maximum line capacity or every service you use. Cancelling, hiding the tab or leaving this screen stops the active test.</p></details>
    </>}
    {view === "network" && <>
      <Heading eyebrow="THE NETWORK THE INTERNET SEES" title="Your public connection details." description="An optional lookup from this browser. No account, API key or background monitoring." />
      <section className="ns-glass ns-tool-panel"><h2>Know which network you appear on.</h2><p>A VPN, proxy, mobile carrier or shared network may change the apparent organization and location. Geolocation is approximate and cannot identify your physical address.</p>
        <label className="ns-consent"><input type="checkbox" checked={networkConsent} disabled={networkBusy} onChange={e => setNetworkConsent(e.target.checked)} /><span>Ask <a href="https://ipwhois.io/privacy" target="_blank" rel="noreferrer">ipwho.is</a> for this browser’s public IP, network organization and approximate region. The service receives my public IP.</span></label>
        <div className="ns-tool-actions"><button className="ns-button ns-primary" disabled={!networkBusy && (!networkConsent || lookupCooldown)} onClick={networkBusy ? () => networkController.current?.abort() : startLookup}>{networkBusy ? "Cancel lookup" : lookupCooldown ? "Wait one minute to look up again" : "Look up my network"}</button><button className="ns-button ns-outline" onClick={() => { networkController.current?.abort(); setNetwork(null); setNetworkConsent(false); setNetworkNotice("Lookup disabled and current details cleared."); }}>Disable & clear lookup</button></div>
        <p role="status" className="ns-tool-status">{networkNotice || "Details remain in this tab only. No lookup is performed when exporting a report."}</p>
      </section>
      <section className="ns-glass ns-tool-panel"><h2>{network ? "Observed public details" : "Nothing looked up yet."}</h2><dl className="ns-network-grid">{[["Public IPv4", network?.family === "IPv4" ? network.ip : "Not observed"], ["Public IPv6", network?.family === "IPv6" ? network.ip : "Not observed"], ["Network organization", network?.organization ?? "Unavailable"], ["ASN", network?.asn ?? "Unavailable"], ["Approximate region", network ? [network.city, network.region, network.country].filter(Boolean).join(", ") || "Unavailable" : "Unavailable"], ["Lookup source", network ? `ipwho.is · ${date(network.at)}` : "Not requested"]].map(([label, detail]) => <div key={label}><dt>{label}</dt><dd>{detail}</dd></div>)}</dl><p>A single lookup reports the address family used for that request. An unobserved IPv4 or IPv6 address does not prove that your connection lacks it. Provider data may be incomplete or outdated.</p>{network && <button className="ns-button ns-outline" onClick={() => onNavigate("reports")}>Create a redacted PDF</button>}</section>
    </>}
    {view === "reports" && <Reports checks={checks} speeds={speeds} network={network} />}
    {view === "companion" && <>
      <Heading eyebrow="ONE WEBSITE. A DEEPER LOCAL VIEW." title="Meet your Windows companion." description="Understand which applications use your connection and manage explicitly chosen local controls." />
      <section className="ns-glass ns-tool-panel"><span className="ns-tag">WINDOWS · SEPARATE INSTALLATION · UNSIGNED</span><h2>Go from “something is using data” to a useful next step.</h2><p>The public website helps with connection problems. The installed companion adds approximate per-application usage, daily and monthly quotas, local connection history, Microsoft Defender information and user-triggered scans.</p>{release ? <a className="ns-button ns-primary" href={release.url} rel="noreferrer"><Icon name="download" />Download Windows companion {release.version}</a> : <p className="ns-notice" role="status">A verified download has not been published yet. The release is being prepared; no installer is downloaded automatically.</p>}<p>This is a source distribution with an installer, requiring Windows 10/11 and Python 3.11. It is unsigned; Windows may show a warning. Review the release notes and checksum before installation.</p></section>
      <section className="ns-glass ns-tool-panel"><h2>Setup, in a few clear steps</h2><ol className="ns-setup-list"><li><strong>Install prerequisites.</strong> Use Python 3.11. Packet attribution additionally needs a separately installed Npcap driver and explicit capture permission. The installer must never silently install a driver.</li><li><strong>Extract the release and read README.</strong> Follow the included installation instructions. Start the ordinary companion dashboard as your standard Windows user.</li><li><strong>Connect locally.</strong> Open the loopback address printed by the launcher and enter the local token it provides. This public site never requests that token or contacts the agent.</li><li><strong>Start with observation.</strong> Choose the available interface and explicitly start collection. Application attribution is approximate; unmatched traffic stays unassigned. It is not ISP billing data.</li><li><strong>Enable controls only when needed.</strong> Firewall changes and Defender scans use the separate privileged agent with explicit elevation. Blocking is opt-in. Scans are performed by Microsoft Defender.</li><li><strong>Stop and uninstall safely.</strong> Follow the release’s stop, cleanup and uninstall commands to remove only NetSentinel-owned firewall rules. Keep the recovery instructions for an interrupted session.</li></ol></section>
      <section className="ns-glass ns-tool-panel"><h2>Your local data stays local.</h2><p>Local monitoring stores bounded metadata and usage totals, not packet payloads, messages, passwords or browsing URLs. Local reports hide addresses and executable paths unless you choose to include them. An unusual pattern is not proof of malware, and no application is blocked because of an anomaly score.</p><p>The website and the local dashboard are separate security boundaries. Never paste a companion token into a public website or share it in a report.</p><a href="https://github.com/hariharan4814/NetSentinel-upgraded" target="_blank" rel="noreferrer">Read source code and project documentation</a></section>
    </>}
  </>;
}

function delta(a: number | null, b: number | null) { return a === null || b === null ? "unavailable" : `${a - b >= 0 ? "+" : ""}${value(a - b)}`; }
function Heading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) { return <div className="ns-page-heading"><div><p className="ns-eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div></div>; }

function Reports({ checks, speeds, network }: { checks: Check[]; speeds: SpeedResult[]; network: NetworkDetails | null }) {
  const [from, setFrom] = useState(() => new Date(Date.now() - 30 * 86_400_000).toISOString().slice(0, 10));
  const [to, setTo] = useState(() => new Date().toISOString().slice(0, 10));
  const [includeChecks, setIncludeChecks] = useState(true), [includeSpeeds, setIncludeSpeeds] = useState(true), [includeNetwork, setIncludeNetwork] = useState(false);
  const [includeIp, setIncludeIp] = useState(false), [includeLocation, setIncludeLocation] = useState(false);
  const [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  async function download() {
    setBusy(true); setNotice("");
    try { const { downloadPublicPdf } = await import("@/lib/public-report"); await downloadPublicPdf({ checks, speeds, network, from, to, includeChecks, includeSpeeds, includeNetwork, includeIp, includeLocation }); setNotice("PDF created. Check your browser’s downloads. It contains only the selected data available in this browser."); }
    catch (error) { setNotice(error instanceof Error ? error.message : "Could not create the PDF. Try again in an up-to-date browser."); }
    finally { setBusy(false); }
  }
  return <><Heading eyebrow="USEFUL WHEN YOU NEED SUPPORT" title="A report worth sharing." description="Create a readable PDF from measurements you already have. Nothing new is measured or looked up during export." /><section className="ns-glass ns-tool-panel"><h2>Choose what to include</h2><div className="ns-report-dates"><label>From (UTC)<input type="date" value={from} onChange={e => setFrom(e.target.value)} /></label><label>To (UTC)<input type="date" value={to} onChange={e => setTo(e.target.value)} /></label></div><p>The report includes the current result plus retained history within these dates. Expired or unsaved past data cannot be recovered.</p><fieldset className="ns-report-options"><legend>Public browser sections</legend><label><input type="checkbox" checked={includeChecks} onChange={e => setIncludeChecks(e.target.checked)} /> Connection checks ({checks.length} available)</label><label><input type="checkbox" checked={includeSpeeds} onChange={e => setIncludeSpeeds(e.target.checked)} /> Speed tests ({speeds.length} available)</label><label><input type="checkbox" checked={includeNetwork} onChange={e => setIncludeNetwork(e.target.checked)} /> Network details ({network ? "current lookup" : "unavailable"})</label></fieldset><fieldset className="ns-report-options"><legend>Private details — hidden by default</legend><label><input type="checkbox" checked={includeIp} disabled={!includeNetwork} onChange={e => setIncludeIp(e.target.checked)} /> Include my public IP address</label><label><input type="checkbox" checked={includeLocation} disabled={!includeNetwork} onChange={e => setIncludeLocation(e.target.checked)} /> Include approximate location</label></fieldset><p>Application usage, Windows security and scan reports are created in the installed companion. They are not available to this website.</p><button className="ns-button ns-primary" disabled={busy || (!includeChecks && !includeSpeeds && !includeNetwork)} onClick={download}><Icon name="download" />{busy ? "Creating PDF…" : "Download PDF"}</button><p role="status" className="ns-tool-status">{notice}</p></section></>;
}
