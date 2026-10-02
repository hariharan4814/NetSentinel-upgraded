"""Semantic paginated PDF reports. Private identifiers are opt-in, never implicit."""
from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
import unicodedata
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String


def text(value):
    # Standard PDF fonts are portable; explicitly disclose normalization below.
    return unicodedata.normalize("NFKD", str(value)).encode("ascii", "replace").decode()


def stamp(value):
    if value is None:
        return "Unavailable"
    if isinstance(value, str):
        return value
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def create_report(snapshot, sections, include_sensitive=False):
    if snapshot.get("mode") not in {"LIVE", "SIMULATION", "REPLAY"}:
        raise ValueError("Report requires explicit provenance")
    stream = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Cell", fontName="Helvetica", fontSize=8, leading=11, wordWrap="CJK"))
    styles.add(ParagraphStyle("Note", fontName="Helvetica", fontSize=8, leading=12, textColor=colors.HexColor("#476368")))
    styles["Title"].textColor = colors.HexColor("#12474b")
    styles["Heading2"].textColor = colors.HexColor("#12474b")
    styles["BodyText"].leading = 14
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=54, bottomMargin=48,
                            title="NetSentinel local observation report", author="NetSentinel")
    story = []
    def p(value, style="BodyText"):
        return Paragraph(escape(text(value)).replace("\n", "<br/>"), styles[style])
    def section(title):
        story.append(Paragraph(title, styles["Heading2"]))
    def table(headers, rows, widths):
        data = [[p(cell, "Cell") for cell in headers]]
        data += [[p(cell, "Cell") for cell in row] for row in rows]
        grid = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        grid.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),colors.HexColor("#dcebe7")),
                                 ("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),8),
                                 ("TOPPADDING",(0,0),(-1,-1),8),("LINEBELOW",(0,0),(-1,-1),.4,colors.HexColor("#d5e0de"))]))
        story.extend([grid, Spacer(1, 12)])
    mode = snapshot["mode"]
    story.append(Paragraph("NetSentinel", styles["Title"]))
    story.append(p("Local observation report", "Heading2"))
    story.append(p(f"{mode} | Installed Windows companion | Schema companion-v1"))
    if mode != "LIVE":
        story.append(p("LABELLED TEST DATA. This example is not a measurement of a user's computer.", "Note"))
    period = snapshot["period"]
    story.append(p(f"Report period: {stamp(period['start'])} through {stamp(period['end'])}"))
    story.append(p(f"Generated: {stamp(snapshot['generated_at'])}"))
    story.append(p("Privacy: executable paths and remote addresses " + ("INCLUDED by explicit request." if include_sensitive else "HIDDEN. Executable display names remain visible."), "Note"))
    story.append(Spacer(1, 12))
    apps = {app["id"]: app for app in snapshot.get("apps", [])}
    def appname(app):
        item = apps.get(app)
        return (item["path"] if include_sensitive else item["name"]) if item else "Unassigned"
    if "usage" in sections:
        section("Application usage")
        story.append(p("Approximate packet-to-socket attribution; observed IP bytes, not payload bytes or ISP billable usage. Daily buckets are UTC. A record with no traffic is different from missing observation.", "Note"))
        totals = defaultdict(lambda: [0, 0])
        for row in snapshot.get("usage", []):
            totals[row["app"]][0] += row["up"]
            totals[row["app"]][1] += row["down"]
        ordered = sorted(totals.items(), key=lambda item: sum(item[1]), reverse=True)
        if not ordered:
            story.append(p("No retained usage observations in this period. Usage is unavailable, not measured zero."))
        else:
            chart = Drawing(510, 30+len(ordered[:8])*23)
            peak = max(sum(values) for _, values in ordered[:8]) or 1
            for i, (app, values) in enumerate(ordered[:8]):
                y = chart.height-30-i*23
                label = text(apps.get(app, {}).get("name", "Unassigned"))
                if len(label) > 31:
                    label = label[:17]+"..."+label[-11:]
                chart.add(String(0,y,label,fontName="Helvetica",fontSize=8))
                chart.add(Rect(155,y-2,240*sum(values)/peak,10,fillColor=colors.HexColor("#2a8b83"),strokeColor=None))
                chart.add(String(405,y,f"{sum(values)/1048576:.3f} MiB",fontName="Helvetica",fontSize=8))
            story.append(KeepTogether([p("Top observed applications - combined IP bytes (MiB)", "Note"),chart]))
            table(["Application", "Upload bytes", "Download bytes", "Combined bytes"],
                  [[appname(app), f"{v[0]:,}", f"{v[1]:,}", f"{sum(v):,}"] for app,v in ordered], [221,98,98,98])
        story.append(p("Current quota settings (as of generation; not historical settings)", "Note"))
        table(["Executable", "Daily / monthly bytes", "Warning / mode"],
              [[appname(a["id"]), f"{a.get('daily') or 'none'} / {a.get('monthly') or 'none'}",
                f"{a.get('warning',80)}% / {'auto-block opted in' if a.get('auto') else 'warnings only'}"] for a in list(apps.values())[:512]] or [["Unavailable","No observed applications","Unavailable"]], [221,170,124])
    if "security" in sections:
        section("Available Windows security and scan status")
        security = snapshot.get("security")
        if not security:
            story.append(p("Windows status has not been queried in this session. No Defender or firewall claim is available."))
        else:
            story.append(p(f"Latest queried snapshot: {stamp(security.get('observed_at'))}. This is not a history of protection throughout the report period. Query success is not a safety verdict.", "Note"))
            defender = security.get("defender", {})
            rows = [["Defender state", defender.get("state", "unavailable")],
                    ["Real-time protection", {True:"Enabled",False:"Disabled",None:"Unavailable"}.get(defender.get("realtime_enabled"), "Unavailable")],
                    ["Signature updated", stamp(defender.get("signature_updated_at"))],
                    ["Quick scan last ended", stamp(defender.get("quick_scan_ended_at"))],
                    ["Full scan last ended", stamp(defender.get("full_scan_ended_at"))]]
            for profile in security.get("firewall", {}).get("profiles", []):
                rows.append([profile["name"]+" firewall", {True:"Enabled",False:"Disabled",None:"Unavailable"}.get(profile.get("enabled"), "Unavailable")])
            table(["Windows interface", "Available observation"],rows,[190,325])
        scan = snapshot.get("scan")
        if scan:
            request = scan.get("request")
            story.append(p("Tracked request: " + (f"{request['kind']} / {request['state']}" if request else "none; ownership unknown after restart")))
            detection = scan.get("detections", {})
            story.append(p("Defender detection history is not attributable to a particular scan. NetSentinel provides no percentage progress or custom remediation.", "Note"))
            items = []
            for item in detection.get("items", []):
                try:
                    at = datetime.fromisoformat(item.get("detected_at") or "").timestamp()
                except ValueError:
                    continue
                if period["start"] <= at <= period["end"]:
                    items.append([item["threat_id"], stamp(at), str(item.get("action_success", "Unavailable"))])
            table(["Threat ID", "Detection time", "Action successful"],items or [["No available records in period","Unavailable is not a clean verdict","Unavailable"]],[150,230,135])
        else:
            story.append(p("Scan observations have not been requested in this session."))
    if "connections" in sections:
        section("Observed flow segments and traffic alerts")
        story.append(p("At most 500 retained flow segments, not confirmed complete connections. Segment bytes are associated observations, not lifetime connection totals. Addresses are hidden unless explicitly included.", "Note"))
        table(["Observed UTC", "Application / protocol", "Remote endpoint", "Up / down bytes"],
              [[stamp(f["at"]), appname(f["app"])+" / "+f["protocol"], f"{f['remote']}:{f['port']}" if include_sensitive else "[address hidden]", f"{f['up']} / {f['down']}"] for f in snapshot.get("flows", [])]
              or [["Unavailable","No retained flow segments","Unavailable","Unavailable"]], [116,169,140,90])
        alerts = [e for e in snapshot.get("events", []) if e["category"] == "security"]
        table(["Observed UTC", "Evidence-based observation"], [[stamp(e["at"]), e["message"]] for e in alerts] or [["None retained", "No alert is not a safety verdict."]], [116,399])
    if "actions" in sections:
        section("Quota warnings and control actions")
        selected = [e for e in snapshot.get("events", []) if e["category"] != "security"]
        table(["Observed UTC", "Category", "Action / available outcome"], [[stamp(e["at"]), e["category"], e["message"]] for e in selected] or [["Unavailable","No retained actions","No action history in this period."]], [116,80,319])
        story.append(p("Rule application is not verified traffic blocking. Automatic blocking requires explicit enforcement and quota opt-in. Statistical anomalies never trigger blocks.", "Note"))
    section("Method and limits")
    story.append(p(snapshot.get("limits", "Local retained metadata only."), "Note"))
    capture = snapshot.get("capture", {})
    story.append(p(f"Capture state at generation: {capture.get('state','unavailable')}. Last observed packet: {stamp(capture.get('last_packet_at'))}. This current state does not reconstruct past capture gaps. Kernel loss remains unknown.", "Note"))
    story.append(p("Measurement versions: packet-socket-approx-v1; companion-v1; descriptive traffic rules v1. Existing host-v1 Isolation Forest research remains separate: its unusualness is not malware probability. Standard PDF font text is normalized to ASCII; unsupported characters may appear as ?. No packet payloads, browsing URLs or credentials are exported.", "Note"))
    def page(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5e0de"))
        canvas.line(40, A4[1]-36, A4[0]-40, A4[1]-36)
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.HexColor("#476368"))
        canvas.drawString(40,A4[1]-27,"NETSENTINEL / LOCAL REPORT / "+mode)
        canvas.drawString(40,27,"Private identifiers "+("included" if include_sensitive else "hidden")+" | Review before sharing")
        canvas.drawRightString(A4[0]-40,27,f"Page {document.page}")
        canvas.restoreState()
    doc.build(story,onFirstPage=page,onLaterPages=page)
    return stream.getvalue()
