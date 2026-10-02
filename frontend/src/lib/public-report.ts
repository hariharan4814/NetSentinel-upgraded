import { jsPDF } from "jspdf";
import { autoTable } from "jspdf-autotable";
import { summarize, type Check } from "./connection-check";
import type { NetworkDetails, SpeedResult } from "./public-measurements";

export type PublicReportOptions = {
  checks: Check[]; speeds: SpeedResult[]; network: NetworkDetails | null;
  from: string; to: string; includeChecks: boolean; includeSpeeds: boolean;
  includeNetwork: boolean; includeIp: boolean; includeLocation: boolean;
  generatedAt?: string; example?: boolean;
};
const number = (value: number | null, places = 2) => value === null ? "Unavailable" : value.toFixed(places);
// Core PDF fonts support Latin-1. Keep identifiers safe and disclose fallback;
// don't pretend missing glyphs are a faithful rendering of an original name.
export const pdfText = (text: string) => text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^\x20-\x7e\n]/g, "?").slice(0, 500);
export function publicReportModel(options: PublicReportOptions) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(options.from) || !/^\d{4}-\d{2}-\d{2}$/.test(options.to)) throw new Error("Choose a valid report date range.");
  const start = Date.parse(`${options.from}T00:00:00Z`), end = Date.parse(`${options.to}T23:59:59.999Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || new Date(start).toISOString().slice(0, 10) !== options.from || new Date(end).toISOString().slice(0, 10) !== options.to || start > end) throw new Error("The start date must be valid and on or before the end date.");
  const within = (at: string) => { const time = Date.parse(at); return time >= start && time <= end; };
  const speeds = options.includeSpeeds ? options.speeds.filter(s => within(s.at)).slice(0, 31) : [];
  const checks = options.includeChecks ? options.checks.filter(c => within(c.at)).slice(0, 11) : [];
  const network = options.includeNetwork && options.network && within(options.network.at) ? {
    source: options.network.source, at: options.network.at, organization: options.network.organization, asn: options.network.asn,
    ip: options.includeIp ? options.network.ip : "Hidden by default",
    family: options.network.family,
    location: options.includeLocation ? [options.network.city, options.network.region, options.network.country].filter(Boolean).join(", ") || "Unavailable" : "Hidden by default",
  } : null;
  return { speeds, checks, network, period: `${options.from} to ${options.to} (UTC)`, generatedAt: options.generatedAt ?? new Date().toISOString(), example: options.example ?? false };
}

export function createPublicPdf(options: PublicReportOptions) {
  const model = publicReportModel(options);
  const doc = new jsPDF({ unit: "mm", format: "a4", compress: false });
  doc.setProperties({ title: "NetSentinel connection report", author: "NetSentinel", subject: model.example ? "SIMULATION - labelled non-private QA data" : "Public browser measurements" });
  let y = 20;
  const paragraph = (text: string) => {
    doc.setFont("helvetica", "normal"); doc.setFontSize(9.5); doc.setTextColor(48, 65, 65);
    const lines: string[] = doc.splitTextToSize(pdfText(text), 174);
    for (const line of lines) { if (y > 269) { doc.addPage(); y = 20; } doc.text(line, 18, y); y += 5; }
    y += 3;
  };
  const heading = (text: string) => {
    if (y > 247) { doc.addPage(); y = 20; }
    y += 4; doc.setFont("helvetica", "bold"); doc.setFontSize(14); doc.setTextColor(16, 89, 77); doc.text(text, 18, y); y += 9;
  };
  const table = (head: string[], body: string[][]) => {
    autoTable(doc, { startY: y, head: [head], body: body.map(row => row.map(pdfText)), margin: { left: 18, right: 18, top: 20, bottom: 22 }, theme: "striped", styles: { font: "helvetica", fontSize: 8, cellPadding: 3, overflow: "linebreak" }, headStyles: { fillColor: [16, 89, 77], textColor: 255 }, rowPageBreak: "avoid" });
    y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
  };
  doc.setFont("helvetica", "bold"); doc.setFontSize(24); doc.setTextColor(16, 89, 77); doc.text("NetSentinel", 18, y); y += 10;
  doc.setFontSize(17); doc.text("Connection report", 18, y); y += 9;
  paragraph(`Period: ${model.period}\nGenerated: ${model.generatedAt}\nScope: PUBLIC BROWSER${model.example ? " / SIMULATION - NON-PRIVATE TEST DATA" : ""}`);
  paragraph("A snapshot for troubleshooting and comparison. No application traffic, Defender status, malware scans or firewall state is available to this public website. Local sections require the separately installed companion.");
  if (options.includeSpeeds) {
    heading("Internet speed measurements");
    paragraph("Source: Cloudflare edge, HTTPS transfers started by the browser. Mbps uses decimal megabits per second. Latency is median HTTP timing; jitter is the mean absolute difference between adjacent successful latency samples. These are not ICMP ping, packet loss, maximum line capacity or ISP billable usage.");
    if (!model.speeds.length) paragraph("No speed results available in the selected period.");
    else {
      table(["Time (UTC)", "State", "Down Mbps", "Up Mbps", "Latency ms", "Jitter ms"], model.speeds.map(s => [s.at.replace("T", " ").slice(0, 19), s.status, number(s.downloadMbps), number(s.uploadMbps), number(s.latencyMs), number(s.jitterMs)]));
      table(["Time (UTC)", "Received body MB", "Confirmed upload MB", "Accounting"], model.speeds.map(s => [s.at.replace("T", " ").slice(0, 19), number(s.receivedBodyBytes === null ? null : s.receivedBodyBytes / 1e6, 3), number(s.confirmedUploadBytes / 1e6, 3), s.accountingIncomplete ? "Partial / lower bound" : "Completed payloads"]));
      const chart = model.speeds.filter(s => s.downloadMbps !== null).slice(0, 8).reverse();
      if (chart.length) {
        if (y + chart.length * 9 + 20 > 267) { doc.addPage(); y = 20; }
        heading("Download comparison (Mbps)");
        const max = Math.max(1, ...chart.map(s => s.downloadMbps!));
        doc.setFont("helvetica", "normal"); doc.setFontSize(8);
        for (const row of chart) { doc.setTextColor(48, 65, 65); doc.text(row.at.slice(5, 16).replace("T", " "), 18, y + 3); doc.setFillColor(63, 145, 125); doc.rect(49, y, row.downloadMbps! / max * 108, 4, "F"); doc.text(number(row.downloadMbps), 161, y + 3); y += 9; }
        y += 4;
      }
    }
    paragraph("Received bytes use browser-reported decoded response bodies when available. Confirmed upload bytes count payloads with a completed server response. Cancelled, failed or retried requests can transfer additional uncounted bytes. Protocol overhead and retransmissions are unavailable. Short single-connection transfers can understate fast links; compare tests under similar conditions.");
  }
  if (options.includeChecks) {
    heading("Lightweight connection checks");
    if (!model.checks.length) paragraph("No connection checks available in the selected period.");
    else table(["Time (UTC)", "Source", "Answered", "Median ms", "Range ms"], model.checks.map(c => { const summary = summarize(c.probes); return [c.at.replace("T", " ").slice(0, 19), model.example ? "SIMULATION" : c.scope, `${summary.success}/${summary.total}`, number(summary.median), number(summary.spread)]; }));
    paragraph("Eight small requests to this website. Range = slowest minus fastest successful response. Failed requests remain missing. LOCAL checks describe the local app only; LIVE checks describe the path to this site. Neither proves the cause of a connection problem.");
  }
  if (options.includeNetwork) {
    heading("Public network details");
    if (!model.network) paragraph("Network lookup unavailable or outside the selected period. No lookup is triggered by a report.");
    else table(["Field", "Observed value"], [["Lookup source", model.network.source], ["Observed (UTC)", model.network.at], ["Address family", model.network.family], ["Public IP", model.network.ip], ["Network organization", model.network.organization ?? "Unavailable"], ["ASN", model.network.asn ?? "Unavailable"], ["Approximate location", model.network.location]]);
    paragraph("The provider sees this browser's apparent public address. VPNs, proxies and shared networks can change the apparent organization and location. Geolocation is approximate, not a physical address. A single lookup may expose only one address family.");
  }
  heading("Privacy and interpretation");
  paragraph(`IP addresses: ${options.includeIp ? "explicitly included where available" : "hidden"}. Location: ${options.includeLocation ? "explicitly included where available" : "hidden"}. No executable paths, browsing URLs or packet payloads are collected by the public tools. Reports stay on your device unless you share them. Built-in PDF fonts transliterate Latin accents and replace unsupported characters with ?.`);
  paragraph("No security verdict or automatic control action is generated from these measurements. Keep downloaded files private, and delete them when no longer needed. NetSentinel does not guarantee internet availability.");
  const count = doc.getNumberOfPages();
  for (let page = 1; page <= count; page++) { doc.setPage(page); doc.setDrawColor(190, 210, 205); doc.line(18, 278, 192, 278); doc.setFontSize(8); doc.setTextColor(80, 100, 96); doc.text(model.example ? "NetSentinel | SIMULATION / NON-PRIVATE QA SAMPLE" : "NetSentinel | Public browser report", 18, 284); doc.text(`${page} / ${count}`, 192, 284, { align: "right" }); }
  return doc;
}

export async function downloadPublicPdf(options: PublicReportOptions) {
  const doc = createPublicPdf(options);
  doc.save(`netsentinel-report-${options.from}-to-${options.to}.pdf`);
}
