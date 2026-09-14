"""Lightweight, evidence-based anomaly explainability for NetSentinel host-v1 features.

Compares observed host feature vectors against the baseline/calibration reference.
Anomalies represent statistical divergence from the baseline, not confirmed attacks.
"""

from typing import Dict, List, Any, Optional

# Empirical reference percentiles derived from the genuine pilot baseline training/calibration sets.
# Features exceeding upper bounds (or outside normal ranges) are flagged with descriptive explanations.
BASELINE_REFERENCE = {
    "packets_per_second": {
        "p95": 80.0,
        "p99": 150.0,
        "max": 200.0,
        "name": "packet rate",
        "unit": "pkt/s",
        "format": lambda v: f"{v:.1f} pkt/s",
    },
    "ip_bytes_per_second": {
        "p95": 60000.0,
        "p99": 120000.0,
        "max": 180000.0,
        "name": "throughput",
        "unit": "bytes/s",
        "format": lambda v: f"{v / 1024:.1f} KiB/s" if v >= 1024 else f"{v:.1f} B/s",
    },
    "outbound_byte_fraction": {
        "p95": 0.95,
        "p99": 0.99,
        "name": "outbound byte fraction",
        "unit": "ratio",
        "format": lambda v: f"{v * 100:.1f}%",
    },
    "unique_remote_peers": {
        "p95": 10.0,
        "p99": 20.0,
        "max": 25.0,
        "name": "unique remote peers",
        "unit": "peers",
        "format": lambda v: f"{int(v)} peers",
    },
    "tcp_syn_fraction": {
        "p95": 0.15,
        "p99": 0.35,
        "name": "TCP SYN fraction",
        "unit": "ratio",
        "format": lambda v: f"{v * 100:.1f}%",
    },
    "udp_fraction": {
        "p95": 0.50,
        "p99": 0.80,
        "name": "UDP fraction",
        "unit": "ratio",
        "format": lambda v: f"{v * 100:.1f}%",
    },
    "mean_ip_packet_bytes": {
        "p95": 1200.0,
        "p99": 1450.0,
        "name": "mean IP packet size",
        "unit": "bytes",
        "format": lambda v: f"{v:.1f} bytes",
    },
}


def explain_anomaly(
    features: Optional[Dict[str, Any]],
    label: str = "NORMAL",
    reference: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate concise, evidence-based feature explanations.

    Rules:
    - Never uses attack, malware, intrusion, or threat attribution language.
    - Uses neutral phrases: 'higher than the learned baseline', 'statistically unusual',
      'outside typical observed range'.
    - Only mentions features that meaningfully deviate from the baseline reference.
    """
    if label == "NORMAL" or not features:
        return {
            "explanation": "Within learned baseline range",
            "deviating_features": [],
        }

    ref = reference or BASELINE_REFERENCE
    deviations: List[str] = []
    deviating_feature_names: List[str] = []

    # 1. Check throughput (ip_bytes_per_second)
    throughput = features.get("ip_bytes_per_second")
    if throughput is not None and throughput > ref["ip_bytes_per_second"]["p95"]:
        fmt = ref["ip_bytes_per_second"]["format"](throughput)
        deviations.append(f"Observed throughput ({fmt}) is higher than the learned baseline range")
        deviating_feature_names.append("ip_bytes_per_second")

    # 2. Check packet rate (packets_per_second)
    pps = features.get("packets_per_second")
    if pps is not None and pps > ref["packets_per_second"]["p95"]:
        fmt = ref["packets_per_second"]["format"](pps)
        deviations.append(f"Observed packet rate ({fmt}) is higher than the learned baseline range")
        deviating_feature_names.append("packets_per_second")

    # 3. Check unique remote peers
    peers = features.get("unique_remote_peers")
    if peers is not None and peers > ref["unique_remote_peers"]["p95"]:
        fmt = ref["unique_remote_peers"]["format"](peers)
        deviations.append(f"Unique remote peer count ({fmt}) is outside typical observed baseline range")
        deviating_feature_names.append("unique_remote_peers")

    # 4. Check TCP SYN fraction
    syn = features.get("tcp_syn_fraction")
    if syn is not None and syn > ref["tcp_syn_fraction"]["p95"]:
        fmt = ref["tcp_syn_fraction"]["format"](syn)
        deviations.append(f"TCP SYN fraction ({fmt}) is elevated relative to the learned baseline")
        deviating_feature_names.append("tcp_syn_fraction")

    # 5. Check UDP fraction
    udp = features.get("udp_fraction")
    if udp is not None and udp > ref["udp_fraction"]["p95"]:
        fmt = ref["udp_fraction"]["format"](udp)
        deviations.append(f"UDP fraction ({fmt}) is statistically unusual relative to baseline")
        deviating_feature_names.append("udp_fraction")

    # 6. Check mean packet size
    mean_bytes = features.get("mean_ip_packet_bytes")
    if mean_bytes is not None and mean_bytes > ref["mean_ip_packet_bytes"]["p95"]:
        fmt = ref["mean_ip_packet_bytes"]["format"](mean_bytes)
        deviations.append(f"Mean IP packet size ({fmt}) is outside typical observed baseline range")
        deviating_feature_names.append("mean_ip_packet_bytes")

    # 7. Check outbound byte fraction
    ob_frac = features.get("outbound_byte_fraction")
    if ob_frac is not None and ob_frac > ref["outbound_byte_fraction"]["p95"]:
        fmt = ref["outbound_byte_fraction"]["format"](ob_frac)
        deviations.append(f"Outbound byte fraction ({fmt}) is statistically unusual relative to baseline")
        deviating_feature_names.append("outbound_byte_fraction")

    if deviations:
        summary = "; ".join(deviations) + "."
    else:
        summary = "Multivariate feature combination is statistically unusual relative to the learned baseline."

    return {
        "explanation": summary,
        "deviating_features": deviating_feature_names,
    }
