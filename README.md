# NetSentinel — Network Visibility, Quota Control & Intelligent Telemetry

NetSentinel delivers three cohesive experiences:
1. **Public Web Utility**: A zero-setup browser tool for everyday users to check connectivity, measure real download/upload speed, look up their provider, follow guided troubleshooting, and export support PDFs.
2. **Windows Companion (Developer Preview 0.2.0)**: A loopback-authenticated desktop dashboard providing per-application traffic accounting, daily/monthly quotas, opt-in Windows Firewall enforcement, Microsoft Defender status & scan controls, and private PDF reports.
3. **Research Network Monitor & Anomaly Engine (`/local`)**: An M.Sc. dissertation system providing host-centric telemetry (Npcap/psutil on `Ethernet 3`), unsupervised Isolation Forest anomaly detection on 7 frozen host-v1 features, and deterministic feature explainability.

**[Open Public NetSentinel](https://netsentinel-connect.hariharan4814.chatgpt.site)** — public deployment confirmed on 2026-10-01.

---

## 1. Public Web Utility (Static Web App)

- **Connectivity Probes**: 8 sequential same-origin HTTP probes measuring median latency, jitter/range, and failure counts.
- **Measured Speed Testing**: User-initiated Cloudflare speed test integration (`@cloudflare/speedtest`) with bounded payload budgets (nominal 15.5 MB, max 62 MB cap). Measures real application throughput, never wire estimates.
- **Visitor Provider Lookup**: Direct client-side `ipapi.co` lookup (consent-gated, default-redacted IP and location).
- **Client-Side Support Reports**: Bounded 7-day browser history and downloadable semantic PDF reports (`jspdf`).
- **Guided Troubleshooting**: Symptom-based step-by-step checklists for slow browsing, video call drops, and complete outages.

### Build and Run Public Frontend
```powershell
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm ci
npm run build
npm run start
```
*Open `http://127.0.0.1:3000` in your browser.*

To generate the strictly allowlisted public static bundle:
```powershell
npm run build:public
```
*Outputs to `public-release/dist` with zero local routes, APIs, or private assets. See [PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).*

---

## 2. Windows Companion (Installed Developer Preview v0.2.0)

- **Traffic Accounting**: Real-time packet-to-socket attribution grouped by canonical SHA-256 executable IDs. Bounded SQLite v1 storage (`companion.sqlite3`).
- **Quotas & Enforcement**: Daily and monthly byte quotas, 80% warning alerts, and opt-in Windows Firewall rules (`NetSecurity` cmdlets). Non-destructive, lease-gated (30s heartbeat expiry), with automatic rollback and recovery (`Recover.ps1`).
- **Windows Security Queries**: Real-time query of Microsoft Defender status (signatures, engine, active protection) and all three Windows Firewall profiles (Domain, Private, Public).
- **Explicit Defender Scans**: User-triggered Quick or Full scans via Defender cmdlets with explicit consent.
- **Private Semantic PDF Reports**: Vector-styled reports via ReportLab with user-selected date ranges and default redaction of file paths and IP addresses.

### Start the Companion Locally
```powershell
cd C:\Users\yuvas\Desktop\NetSentinel
# 1. Initialize local state and tokens:
.\.venv\Scripts\python.exe -m companion init

# 2. Start the companion dashboard service:
.\.venv\Scripts\python.exe -m companion serve
```
*Open `http://127.0.0.1:8765`. Find your local login key in `%LOCALAPPDATA%\NetSentinel\state\access.token`.*

To run the optional privileged broker for firewall rules and Defender scans:
```powershell
# Open an elevated Administrator PowerShell window:
.\companion\packaging\Start-Broker.ps1
```
*See [COMPANION_SETUP.md](docs/COMPANION_SETUP.md) and [COMPANION_UPGRADE.md](docs/COMPANION_UPGRADE.md).*

---

## 3. Local Research Stack & Anomaly Engine (`/local`)

An M.Sc. dissertation project delivering host-centric network telemetry, unsupervised Isolation Forest anomaly detection, deterministic feature-level explainability, and a modern web dashboard.

### Start Backend and Research Dashboard
```powershell
# Terminal 1 - Django REST Backend (port 8001):
cd C:\Users\yuvas\Desktop\NetSentinel
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001

# Terminal 2 - Next.js Local Monitor (port 3000):
cd C:\Users\yuvas\Desktop\NetSentinel\frontend
npm run dev -- -p 3000
```
*Access `/local` at `http://127.0.0.1:3000/local`. Operator sign-in requires credentials configured in `docs/LOCAL_AUTH.md`.*

---

## Automated Test Verification Summary

- **Companion Unit & Integration Tests**: **58 / 58 passing** (`companion/tests/`).
- **Sensor Tests**: **3 / 3 passing** (`tests/`).
- **Backend Django REST Tests**: **56 / 56 passing** (`backend/tests/`). Database migrations clean (`makemigrations --check --dry-run`).
- **Frontend Unit Tests**: **52 / 52 passing** (`frontend/tests/`).
- **Frontend E2E Browser Tests**: **29 / 29 passing**, 1 skipped opt-in (`frontend/tests/browser/`).
- **Code Quality**: ESLint 0 warnings, TypeScript 0 errors, Next.js production build clean.


# Local network monitoring & explainable anomaly detection

An M.Sc. dissertation project delivering host-centric network telemetry, unsupervised Isolation Forest anomaly detection, deterministic feature-level explainability, and a modern, responsive web dashboard on a native Windows laptop.

---

## Project Status: Sprints 0–6 Complete & Verified

| Sprint | Scope | Deliverables & Gates | Status |
|:---|:---|:---|:---:|
| **Sprint 0** | Planning & Architecture | Product requirements, module boundaries, scientific rules, and test strategy | **COMPLETE** |
| **Sprint 1** | Native Windows Sensor | Real Npcap/Scapy packet sniffer on `Ethernet 3`, 1s OS counters, 10s flows, interface loss recovery (93 tests) | **PASS** (`ea8819a`) |
| **Sprint 2** | Django REST + PostgreSQL | Transactional persistence, telemetry/window/status APIs, provenance gating, loopback isolation | **PASS** (`7fb7281`) |
| **Sprint 3** | Next.js Monitoring Dashboard | Real-time rate gauges, traffic charts, session summaries, outage retention, and automatic reconnect | **PASS** (`79ee41b`) |
| **Sprint 4** | Isolation Forest ML Engine | 335 genuine LIVE windows (4 runs, 2 UTC dates), 180 train / 60 cal / 60 test split, calibrated threshold $\tau \approx 0.7191$ | **PASS** (`a7cfdb5`) |
| **Sprint 5** | Explainability & UI Redesign | Lightweight percentile-based feature explainability, neutral vocabulary, light theme design system with Google Roboto | **PASS** (`793ae85`) |
| **Sprint 6** | E2E Integration & Viva Readiness | Full pipeline verification on LIVE Session 4, master documentation, screenshot checklist, and viva defense guide | **COMPLETE** |

**Total Automated Tests:** **209 / 209 passing (100%)** across backend Django tests (50), ML tests (18), sensor tests (93), frontend unit tests (29), and Playwright E2E browser tests (19).

---

## Core Modules & Architecture

```
+-------------------------------------------------------------+
|                     Selected Network Adapter                |
+-------------------------------------------------------------+
                              |
                     (Npcap Packet Stream)
                              v
+-------------------------------------------------------------+
|              Standalone Python Sensor (sensor/)             |
|   - 1-Second OS Counter Telemetry (psutil)                  |
|   - 10-Second Flow Aggregation & Feature Extraction (Scapy) |
|   - Local Console Output + Optional REST Ingestion          |
+-------------------------------------------------------------+
                              |
                    (Loopback REST Ingestion)
                              v
+-------------------------------------------------------------+
|               Django REST Backend (backend/)                |
|   - Bounded PostgreSQL 17 Persistence                       |
|   - AnomalyResult & ModelVersion Metadata Storage           |
|   - Dynamic Feature Explainability Serialization            |
+-------------------------------------------------------------+
                              |
                    (Loopback Same-Origin Gateway)
                              v
+-------------------------------------------------------------+
|               Next.js Dashboard (frontend/)                 |
|   - Clean Light Theme Design System (Roboto Font)           |
|   - Anomaly Status Badge, Score, Threshold & Disclaimer     |
|   - Collapsible History & Real-Time Outage Retention        |
+-------------------------------------------------------------+
```

1. **Live Network Monitor (`sensor/`)**: Standalone Python 3.11 engine using Npcap 1.88 and Scapy 2.7.0. Gathers continuous 1-second OS network counters and 10-second Layer 3/Layer 4 flow aggregations. Works completely offline without backend dependencies.
2. **Anomaly Detection Engine (`ml/`)**: Standalone offline ML pipeline. Uses `scikit-learn` Isolation Forest trained on genuine traffic-derived host features. Scores complete, finalized 10-second windows.
3. **Explainable Threat Analysis (`backend/detection/`)**: Evaluates feature vectors against empirical baseline reference percentiles ($p95$, $p99$) to generate deterministic, human-readable explanations.
4. **Network Recovery & Dashboard (`frontend/`)**: Modern Next.js 16 + React 19 + Framer Motion interface. Features live telemetry gauges, traffic charts, anomaly cards, collapsible history, and robust outage retention.

---

## Seven Frozen Host-v1 Features

All features are extracted strictly from Layer 3 (IP) and Layer 4 (TCP/UDP) packet headers over non-overlapping **10-second event-time windows**:

| Feature Name | Type | Definition & Extraction Semantics |
|:---|:---:|:---|
| `packets_per_second` | Float | Total attributable IP packets in window / window duration (10.0s). |
| `ip_bytes_per_second` | Float | Total IP header + payload bytes / window duration (10.0s). |
| `outbound_byte_fraction` | Float | Outbound IP bytes / (inbound + outbound IP bytes). Range $[0.0, 1.0]$ ($0.0$ if idle). |
| `unique_remote_peers` | Integer | Count of distinct remote IP endpoints observed across all active flows. |
| `tcp_syn_fraction` | Float | TCP packets with SYN flag set / total observed TCP packets ($0.0$ if no TCP). |
| `udp_fraction` | Float | Observed UDP IP packets / total attributable IP packets ($0.0$ if idle). |
| `mean_ip_packet_bytes` | Float | Total IP bytes / total IP packets (average packet size in bytes). |

---

## Machine Learning Methodology & Baseline Model

- **Training Distribution**: 335 genuine LIVE windows gathered from the reference laptop (`Ethernet 3`) across 4 independent capture runs on 2 distinct UTC calendar dates. Zero synthetic records were used in baseline training.
- **Chronological Split**:
  - **Training Set (180 windows)**: Chronologically first segment used to fit the estimator.
  - **Calibration Set (60 windows)**: Subsequent chronological segment used *solely* to select the decision threshold.
  - **Held-out Test Set (60 windows)**: Final chronological segment used for one-time evaluation.
  - **Unused Buffer (35 windows)**: Preserved at the end of the sequence to maintain exact split sizes.
- **Estimator Configuration**: `IsolationForest(n_estimators=100, max_samples=180, random_state=42)`.
- **Calibrated Threshold**: $\tau \approx 0.7190637495$ ($\approx 0.7191$), calibrated using the 99th percentile ($p99$) of baseline calibration anomaly scores.
- **Score Orientation**: Defined as $\text{Anomaly Score} = -\text{score\_samples}(X)$, so that higher scores represent greater statistical divergence ($0.0$ to $1.0$).

### Known Anomalous Demonstration Record (LIVE Session 4)
- **Session UUID**: `59673d80-de26-4f31-a828-d91d97664cf8` (Run `cdca0d58-25bc-43ab-be21-a1b6f38c8844`)
- **Window ID**: `5a5906ff-d994-530b-8cc5-4d243d3c1d9a` (Observed `2026-09-14 02:57:50 UTC`)
- **Anomaly Score**: **`0.7314`** (exceeds threshold `0.7191`)
- **Status**: **`ANOMALOUS`**
- **Evidence Explanation**: *"Observed throughput (685.5 KiB/s) is higher than the learned baseline range; Observed packet rate (892.3 pkt/s) is higher than the learned baseline range; Unique remote peer count (44 peers) is outside typical observed baseline range."*
- **Deviating Features**: `ip_bytes_per_second`, `packets_per_second`, `unique_remote_peers`

---

## Quick-Start & Execution Guide

### Prerequisites
- **OS**: Windows 10/11 (64-bit)
- **Python**: Python 3.11
- **Node.js**: Node.js 20+
- **Packet Capture Driver**: [Npcap 1.80+](https://npcap.com/) (installed with WinPcap compatibility)
- **Database**: PostgreSQL 17 (running locally on port 5432)

---

### 1. Start the Django REST Backend
```powershell
# Navigate to project root
cd c:\Users\yuvas\Desktop\NetSentinel

# Activate backend virtual environment and start server
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001
```
*Backend runs on `http://127.0.0.1:8001`.*

---

### 2. Start the Next.js Frontend Dashboard
```powershell
# In a new terminal, navigate to frontend/
cd c:\Users\yuvas\Desktop\NetSentinel\frontend

# Start Next.js development server
npm run dev -- -p 3000
```
*Dashboard opens on `http://127.0.0.1:3000`.*

---

### 3. Run the Standalone Sensor (Optional Direct Capture)
```powershell
# In a new terminal, activate sensor virtual environment
.\.venv\Scripts\python.exe -m sensor.cli interfaces
.\.venv\Scripts\python.exe -m sensor.cli counters --interface "Ethernet 3" --samples 5
.\.venv\Scripts\python.exe -m sensor.cli capture --interface "Ethernet 3" --duration 10
```

---

## Demonstration Walkthrough (Step-by-Step Viva Presentation)

1. **Open the Dashboard**: Navigate to `http://127.0.0.1:3000` in Google Chrome or Mozilla Firefox.
2. **Initial State**: Observe the clean Light Theme landing page, Google Roboto typography, and empty state cards.
3. **Select Genuine Session 4**:
   - Monitoring session UUID: `59673d80-de26-4f31-a828-d91d97664cf8`
   - Provenance: `LIVE`
   - Click **View session →**.
4. **Inspect Connection & Summary**:
   - Connection chip confirms `Backend reachable` (green dot).
   - Session panel displays interface `Ethernet 3`, observation profile `live_pilot_baseline_host_v1`, and UTC start timestamp.
5. **Inspect Anomaly Detection Panel**:
   - Latest window displays **`NORMAL`** green badge with score `0.4642`.
   - Threshold `0.7191` and Model Version `505fdd6c…` are displayed.
   - Explanation text states: *"Within learned baseline range"*.
   - Mandatory scientific disclaimer is visible:
     > *"Anomaly indicates statistical deviation from the learned baseline, not confirmed malicious activity."*
6. **Inspect Anomaly History & Known Anomalous Window**:
   - Click **Inspect recent anomaly scoring history (45 records)** to expand the table.
   - Locate the highlighted red row (`2026-09-14 02:57:50 UTC`).
   - Score `0.7314` is prominently displayed against threshold `0.7191`.
   - Feature explanation chips identify burst throughput ($685.5\text{ KiB/s}$), packet rate ($892.3\text{ pkt/s}$), and remote peer count ($44\text{ peers}$).
7. **Demonstrate Outage Retention & Recovery**:
   - Temporarily stop the backend server (`Ctrl+C` on port 8001).
   - The connection chip updates to `Backend unavailable` (amber).
   - All historical cards and tables retain their loaded data alongside a clear `Refresh failed` notice (no blanking or zeroing).
   - Restart the backend server. The dashboard automatically recovers without page reload.

---

## Screenshots Checklist for Project Report

When preparing your dissertation report and viva slides, capture the following screenshots:

- [ ] **1. Dashboard Overview / Empty State**: `http://127.0.0.1:3000` before session selection.
- [ ] **2. Live Session 4 Loaded View**: Dashboard showing `Backend reachable`, interface `Ethernet 3`, and top metric cards.
- [ ] **3. Latest Anomaly Status (NORMAL)**: Anomaly hero card with green `NORMAL` badge, score `0.4642`, threshold `0.7191`, and neutral explanation.
- [ ] **4. Expanded Anomaly Scoring History Table**: Table showing historical windows, scores, thresholds, and explanations.
- [ ] **5. Known Anomalous Result Detail**: Highlighted row for window `5a5906ff…` with `ANOMALOUS` red badge, score `0.7314`, and deviating feature chips.
- [ ] **6. Traffic Windows Panel**: 10-second traffic window table with packet, byte, protocol, and flow counts.
- [ ] **7. Capture & Interface Panel**: Status card showing `RUNNING`, valid state, and interface metadata.
- [ ] **8. Backend Outage Retention**: Dashboard displaying amber `Backend unavailable` status while preserving historical data.
- [ ] **9. Standalone Sensor CLI**: PowerShell terminal executing `sensor.cli counters` and `sensor.cli capture`.
- [ ] **10. ML Training Pipeline Summary**: Terminal output from `ml.cli train` displaying model manifest and threshold calibration.

---

## Non-Negotiable Scientific & Privacy Principles

1. **Anomaly != Attack**: An anomaly indicates statistical divergence from a learned baseline. It is never presented as an attack probability, threat level, or malware detection verdict.
2. **Zero Payload Persistence**: Only packet headers and statistical flow metrics are captured. Application payloads, passwords, and sensitive cookies are never logged or stored.
3. **Strict Provenance Partitioning**: `LIVE`, `SIMULATION`, and `REPLAY` modes are strictly partitioned end-to-end. Synthetic records never enter a live baseline.
4. **Missing Data is Not Zero**: Unobserved periods and sensor outages are preserved as explicit monitoring gaps—never zero-filled or smoothed.
5. **No Speculative Terminology**: The UI and backend strictly prohibit uncorroborated security buzzwords ("hacker", "cyber attack", "malware infection", "exfiltration certainty").

---

## Documentation Sitemap

- [Viva Voce Technical Defense Guide](docs/VIVA_GUIDE.md) — Comprehensive viva Q&A and technical rationale.
- [Architecture & ADR Register](docs/ARCHITECTURE.md) — Full system architecture and 27 Architecture Decision Records.
- [Sequential Project Roadmap](docs/ROADMAP.md) — Acceptance gates and completion milestones for Sprints 0–6.
- [Machine Learning Methodology](docs/ML_METHODOLOGY.md) — Isolation Forest training, baseline splits, and threshold calibration.
- [Frozen Live Feature Contract](docs/LIVE_FEATURE_CONTRACT.md) — Mathematical definitions of the 7 host-v1 features.
- [Testing Strategy & Test Matrix](docs/TESTING_STRATEGY.md) — Multi-tier test suite and validation strategy.
- [Windows Sensor Specification](docs/NETWORK_SENSOR_PLAN.md) — Npcap/Scapy integration, OS counters, and recovery bounds.
- [Database Schema & API Plan](docs/DATABASE_PLAN.md) — PostgreSQL models, migrations, and DRF endpoint contracts.
- [Design System & Tokens](docs/DESIGN_SYSTEM.md) — Light theme design tokens, typography, and Framer Motion micro-interactions.
