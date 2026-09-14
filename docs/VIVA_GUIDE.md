# NetSentinel: Viva Voce Preparation & Technical Defense Guide

This guide provides structured, scientifically defensible answers to expected examiner and viva questions for the **NetSentinel** M.Sc. dissertation project.

---

## 1. Project Motivation & Problem Statement

### Q1: What problem does NetSentinel solve?
Traditional Network Intrusion Detection Systems (NIDS) are often opaque black boxes that ingest gigabytes of payload data, rely on outdated signature databases, or claim unrealistic "AI attack classification" on synthetic datasets (e.g., KDD99, CICIDS2017) without testing on real hardware.
**NetSentinel** solves three practical engineering challenges:
1. **Host-Centric Live Observation**: Captures genuine, real-time packet metadata on a standard Windows laptop without requiring specialized networking gear, kernel-level drivers, or cloud infrastructure.
2. **Scientifically Defensible Anomaly Detection**: Uses unsupervised Isolation Forest trained on genuine live traffic baselines to detect *statistical deviations*, explicitly avoiding unverified "attack probability" claims.
3. **Transparent, Lightweight Explainability**: Provides deterministic, feature-level reasons for anomalous windows without slow, non-deterministic LLMs or heavy approximation frameworks (SHAP/LIME).
4. **Zero Payload Storage (Privacy by Design)**: Strictly extracts header metadata and statistical aggregations—never storing raw packet payloads or sensitive user credentials.

### Q2: Why is this system needed if enterprise SIEM / IDS tools already exist?
Enterprise tools (Snort, Suricata, Zeek, Splunk) are designed for dedicated network appliances, enterprise server clusters, and mirrored SPAN ports. They are heavy, resource-intensive, and assume full network visibility. NetSentinel is designed for **own-host laptop observation**, providing a lightweight, explainable, and privacy-preserving security telemetry pipeline suitable for standalone laptops and edge endpoints.

---

## 2. System Architecture & Tech Stack

### Q3: Explain the high-level architecture of NetSentinel.
NetSentinel follows a modular, decoupled architecture consisting of four layers:
1. **Native Windows Sensor (`sensor/`)**: Python 3.11 + Scapy 2.7.0 + Npcap 1.88. Runs independently of the backend. Produces 1-second OS counter telemetry and 10-second packet metadata aggregation windows.
2. **Offline ML Pipeline (`ml/`)**: Standalone CLI pipeline (`ml.cli`) that extracts, reviews, splits, trains, calibrates, and evaluates the Isolation Forest model from genuine live baseline recordings.
3. **Django REST Backend (`backend/`)**: Modular Django 5.1 monolith on PostgreSQL 17. Exposes bounded, strictly validated REST APIs (`/api/v1/telemetry/`, `/api/v1/windows/`, `/api/v1/capture-status/`, `/api/v1/monitoring-sessions/`, `/api/v1/anomaly-results/`, `/api/v1/model-versions/`).
4. **Next.js Local Dashboard (`frontend/`)**: Next.js 16 + React 19 + TypeScript + Framer Motion. Connects via an internal loopback gateway (`/api/backend/*`) enforcing same-origin security and strict runtime schema decoding.

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

### Q4: Why Django + PostgreSQL + Next.js instead of microservices or WebSockets?
- **Django Monolith**: Keeps deployment simple on a student laptop without Docker, Kubernetes, or microservice orchestration overhead.
- **PostgreSQL 17**: Provides transactional ACID durability and relational integrity across sessions, windows, and scores.
- **Next.js App Router**: Provides modern server-side request routing, security gating, and fast static asset delivery.
- **Bounded REST Polling over WebSockets**: REST with explicit backoff (`pollDelay`) and retain-on-error behavior guarantees that backend outages are gracefully handled without dropped socket reconnection loops or memory leaks.

---

## 3. Machine Learning Methodology & The 7 Features

### Q5: Why Isolation Forest?
- **Unsupervised Anomaly Detection**: Network traffic is overwhelmingly benign. Supervised algorithms require massive labelled attack datasets that rarely match real-world environments. Isolation Forest isolates anomalies by randomly partitioning feature space; anomalies require fewer splits to isolate (shorter path lengths in tree ensembles).
- **Fast & Lightweight**: Linear time complexity $O(n \log n)$, low memory footprint, and deterministic reproducibility with a fixed random seed.
- **No Heavy Assumptions**: Does not assume a normal (Gaussian) distribution, unlike parametric statistical tests.

### Q6: What are the seven frozen host-v1 features?
All seven features are extracted over non-overlapping **10-second event-time windows**:
1. `packets_per_second`: Total attributable IP packets / window duration (10s).
2. `ip_bytes_per_second`: Total IP header + payload bytes / window duration (10s).
3. `outbound_byte_fraction`: Outbound IP bytes / total IP bytes ($0.0$ to $1.0$).
4. `unique_remote_peers`: Count of distinct remote IP addresses communicated with during the window.
5. `tcp_syn_fraction`: TCP packets with SYN flag set / total observed TCP packets ($0.0$ to $1.0$).
6. `udp_fraction`: UDP packets / total attributable IP packets ($0.0$ to $1.0$).
7. `mean_ip_packet_bytes`: Total IP bytes / total IP packets (average packet size).

### Q7: Why exactly these 7 features?
- **Coverage of Traffic Dimensions**: They represent volume (bytes/sec), rate (packets/sec), directionality (outbound fraction), connectivity/fan-out (remote peers), transport protocol mix (UDP fraction), connection initiation patterns (TCP SYN fraction), and packet size distribution (mean packet bytes).
- **Header-Only Reconstructibility**: Every feature can be computed strictly from Layer 3/Layer 4 IP/TCP/UDP headers without inspecting application payloads.
- **Robust Against Ephemeral Gaps**: Evaluated in fixed 10-second windows with strict quality flags (`valid=True`, `partial=False`).

---

## 4. Dataset, Splitting & Threshold Calibration

### Q8: How was the pilot baseline model trained?
The pilot model was trained exclusively on **genuine LIVE network traffic** captured on the reference laptop (`Ethernet 3`):
- **Total Dataset Size**: 335 eligible, 10-second LIVE windows.
- **Diversity**: Collected across 4 independent capture runs on 2 distinct UTC calendar dates.
- **Zero Synthetic Pollution**: Absolutely no synthetic, demo, or public benchmark data was mixed into the LIVE training set.

### Q9: What was the data split methodology?
The dataset follows a strict **chronological, session-separated split**:
- **Training Set (180 windows)**: Earliest chronological segment used to fit the Isolation Forest estimator ($n=180$, `max_samples=180`, `n_estimators=100`, `random_state=42`).
- **Calibration Set (60 windows)**: Subsequent chronological segment used *solely* to determine the decision threshold.
- **Held-out Test Set (60 windows)**: Final segment used strictly for one-time evaluation.
- **Unused Buffer (35 windows)**: Kept unassigned to maintain clean, documented split sizes.

### Q10: How was the anomaly threshold selected?
- The threshold was calibrated on the **Calibration Set** using the **99th percentile ($p99$)** of baseline anomaly scores.
- **Calibrated Threshold**: $\tau \approx 0.7190637495$ ($\approx 0.7191$).
- Any future window producing a score $S > \tau$ is classified as `ANOMALOUS`. Windows with $S \le \tau$ are classified as `NORMAL`.

### Q11: Why is the score oriented so that higher = more unusual?
In `scikit-learn`, `score_samples()` returns negative values where lower numbers indicate anomalies. To make the metric intuitive and scientifically transparent for human operators, NetSentinel defines:
$$\text{Anomaly Score} = -\text{score\_samples}(X)$$
Thus, a higher score represents higher divergence from the learned baseline distribution, bounded between $0.0$ and $1.0$.

---

## 5. Anomaly Semantics & The "Anomaly != Attack" Rule

### Q12: Why is an anomaly NOT necessarily an attack?
An anomaly is purely a **mathematical and statistical statement**: *"This 10-second observation deviates significantly from the traffic patterns observed during baseline training."*
- A legitimate high-speed file download, a Steam game update, or video conferencing can produce statistically unusual throughput or packet rates.
- Conversely, a slow and low stealthy attack may blend into normal traffic.
- Labeling every statistical outlier as a "cyber attack" causes severe alert fatigue and false positives. NetSentinel presents anomaly scores as statistical divergence, not threat certainty.

### Q13: What known anomalous result was found in Session 4?
During LIVE Session 4 (`59673d80-de26-4f31-a828-d91d97664cf8`), window `5a5906ff-d994-530b-8cc5-4d243d3c1d9a` produced:
- **Anomaly Score**: $0.7314077498$ (exceeding the threshold $0.7190637495$).
- **Status**: `ANOMALOUS`.
- **Explanation**: *"Observed throughput (685.5 KiB/s) is higher than the learned baseline range; Observed packet rate (892.3 pkt/s) is higher than the learned baseline range; Unique remote peer count (44 peers) is outside typical observed baseline range."*
- **Deviating Features**: `ip_bytes_per_second`, `packets_per_second`, `unique_remote_peers`.

---

## 6. Explainability vs. LLMs & SHAP

### Q14: How does NetSentinel explain anomalies without SHAP/LIME or an LLM?
- **Lightweight Reference-Based Percentile Evaluation**: When a window is scored `ANOMALOUS`, [`backend/detection/explain.py`](file:///c:/Users/yuvas/Desktop/NetSentinel/backend/detection/explain.py) compares its actual feature vector against the empirical baseline distribution ($p95$, $p99$, maximum values).
- **Deterministic & Fast**: Executes in $<1\text{ ms}$ during API serialization without running heavy perturbations or external API calls.
- **Evidence-Based Neutral Language**:
  - ANOMALOUS: Identifies the exact deviating metrics (e.g., *"Observed packet rate (892.3 pkt/s) is higher than the learned baseline range"*).
  - NORMAL: Outputs *"Within learned baseline range"*.
  - Strictly prohibits speculative words ("malware", "threat", "attack", "hacker").

---

## 7. Network Sensor & Interface Recovery

### Q15: How does the sensor handle packet capture vs. OS counters?
- **1-Second OS Counters (psutil)**: Polled continuously from the Windows kernel network stack (`bytes_sent`, `bytes_received`, `packets_sent`, `packets_received`). Provides instant rate visibility even when packet capture is idle or encountering driver issues.
- **10-Second Packet Aggregation (Scapy + Npcap)**: Operates an asynchronous packet sniffer on the selected adapter, aggregating Layer 3/Layer 4 headers into active bidirectional flow tables and extracting 7-feature vectors.

### Q16: How does interface loss and automatic recovery work?
If a network cable is unplugged or Wi-Fi drops:
1. The sensor detects socket errors, zero counter progress, or interface state transitions.
2. It transitions state to `INTERFACE_LOST`, records `loss_started_at`, and invalidates active incomplete windows (marking them `partial=True, valid=False`).
3. It enters a bounded recovery loop (`RECOVERING`), retrying adapter binding with exponential backoff up to a configured deadline.
4. Once restored, it logs the total `monitoring_gap_seconds`, resets counter baselines, and resumes `RUNNING`.
5. Missing data during the outage is explicitly marked as a gap—never zero-filled or fabricated.

---

## 8. Privacy & Security Principles

### Q17: How does NetSentinel preserve user privacy?
- **Zero Payload Persistence**: The Scapy sniffer runs with `store=False`, discarding packet payload bytes immediately after parsing IP/TCP/UDP headers.
- **Metadata Aggregation**: Only flow keys (IP, port, protocol), byte counts, packet counts, and statistical summaries are retained.
- **No Sensitive Credential Logging**: Passwords, HTTP cookies, authentication tokens, and private payload contents never touch disk or database.
- **Loopback-Only Isolation**: Backend and frontend services bind strictly to `127.0.0.1`. The Next.js gateway blocks cross-origin requests, CSRF attacks, and DNS rebinding.

---

## 9. Limitations & Future Enhancements

### Q18: What are the current limitations of the project?
1. **Single Observation Point**: Observes traffic from one selected network interface on the host laptop; cannot see traffic between other devices on the LAN without port mirroring.
2. **Pilot Baseline Scale**: The 335-window pilot baseline covers initial working sessions; production deployment would benefit from multi-week continuous baselining across diurnal/seasonal cycles.
3. **Marginal Feature Explanations**: Explainability evaluates marginal feature deviations against reference percentiles rather than high-dimensional tree interaction paths.

### Q19: What future enhancements could be added?
1. **Multi-Interface Aggregation**: Simultaneous capture across Wi-Fi and Ethernet with unified interface attribution.
2. **Online Incremental Learning**: Adaptive baseline updating using streaming algorithms (e.g., Half-Space Trees or Streaming Random Cut Forests) with concept drift detection.
3. **Encrypted Flow Profiling**: Extension of feature set to include TLS Client Hello metadata (JA3/JA4 fingerprints) and packet size sequence analysis for encrypted traffic without decryption.
