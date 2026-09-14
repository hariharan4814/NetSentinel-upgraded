"""Read actual sensor CLI JSONL; recompute all seven values from retained metadata."""
import hashlib
import ipaddress
import json
from collections import Counter
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

from sensor.features import host_features
from sensor.flows import Flow, Window
from sensor.models import infer_direction
from backend.detection.contract import FEATURE_NAMES, SCHEMA, eligible, profile, finite


def iso(seconds):
    return datetime.fromtimestamp(finite(seconds), timezone.utc).isoformat()


def convert(record, started, source_id, observation_profile):
    """Require full flow evidence, even when a producer supplied a feature vector."""
    if record.get("partial") is not False or record.get("features") is None:
        raise ValueError("partial_or_missing_features")
    if record.get("schema_version") != "phase1b-flow-v1" or record.get("feature_schema_version") != SCHEMA:
        raise ValueError("unsupported_feature_or_flow_schema")
    for key in ("run_id", "session_id", "mode"):
        if record[key] != started[key]:
            raise ValueError("capture_session_identity_mismatch")
    if record["interface"] not in (started["interface"], started.get("capture_interface")):
        raise ValueError("capture_session_identity_mismatch")
    if started["schema_version"] != "phase1b-capture-v1" or started["kernel_loss"] != "unknown":
        raise ValueError("unsupported_capture_context")
    raw_flows = record["flows"]
    if not isinstance(raw_flows, list) or len(raw_flows) > 10000:
        raise ValueError("invalid_flow_collection")
    flow_fields = {f.name for f in fields(Flow)}
    flows = {}
    for f in raw_flows:
        if set(f) != flow_fields | {"protocol", "endpoint_a", "endpoint_b"}:
            raise ValueError("missing_or_extra_flow_metadata")
        if f["protocol"] not in ("TCP", "UDP") or f["incomplete"] is not False:
            raise ValueError("incomplete_transport_metadata")
        endpoints = []
        for key in ("endpoint_a", "endpoint_b"):
            endpoint = f[key]
            if not isinstance(endpoint, (list, tuple)) or len(endpoint) != 2 or type(endpoint[1]) is not int or not 0 <= endpoint[1] <= 65535:
                raise ValueError("missing_transport_endpoint")
            if str(ipaddress.ip_address(endpoint[0])) != endpoint[0]:
                raise ValueError("noncanonical_endpoint")
            endpoints.append(tuple(endpoint))
        key = (record["interface"], f["protocol"], *endpoints)
        if key in flows or endpoints != sorted(endpoints):
            raise ValueError("duplicate_or_unsorted_flow")
        direction = infer_direction(endpoints[0][0], endpoints[1][0], record["local_addresses"])
        if direction == "unknown":
            raise ValueError("unknown_direction")
        for name in ("packets", "ip_bytes", "outbound_packets", "outbound_bytes", "inbound_packets", "inbound_bytes", "unknown_packets", "tcp_syn_packets"):
            if type(f[name]) is not int or f[name] < 0:
                raise ValueError("invalid_flow_counter")
        if (f["packets"] <= 0 or f["unknown_packets"] or f["tcp_syn_packets"] > f["packets"]
                or f["protocol"] == "UDP" and f["tcp_syn_packets"] != 0
                or f["packets"] != f["outbound_packets"] + f["inbound_packets"]
                or f["ip_bytes"] != f["outbound_bytes"] + f["inbound_bytes"]
                or not record["start"] <= finite(f["first_observed"]) <= finite(f["last_observed"]) < record["end"]):
            raise ValueError("inconsistent_flow_metadata")
        flows[key] = Flow(**{k: f[k] for k in flow_fields})
    reconstructed = host_features(Window(start=record["start"], mode=record["mode"], session_id=record["session_id"],
                                          interface=record["interface"], flows=flows, partial=False,
                                          dropped=record["dropped"], finalized_at=record["finalized_at"]), record["local_addresses"])
    # Peers are distinct remote IPs from the endpoints; SYN fraction uses per-flow tcp_syn_packets.
    if reconstructed is None or reconstructed != record["features"]:
        raise ValueError("supplied_features_disagree_with_flow_reconstruction")
    # Bound endpoint/SYN evidence, but do not retain endpoint tuples in exported rows.
    session = {"session_id": record["session_id"], "run_id": record["run_id"], "source_id": str(UUID(source_id)),
               "interface_name": started["interface"], "mode": record["mode"], "started_at": iso(started["observed_at"]),
               "observation_profile": observation_profile, "schema_version": "backend-v1"}
    if not isinstance(observation_profile, str) or not 1 <= len(observation_profile) <= 80:
        raise ValueError("explicit_observation_profile_required")
    window = {k: session[k] for k in ("session_id", "run_id", "interface_name", "mode")}
    window.update({"id": str(uuid5(NAMESPACE_URL, f"netsentinel:window:{record['session_id']}:{record['start']}")),
                   **{k: iso(record[k]) for k in ("start", "end", "finalized_at", "processed_at")},
                   "measurement_source": record["measurement_source"], "schema_version": "backend-window-v1",
                   "partial": False, "valid": True, "reason": None, "dropped": record["dropped"],
                   "kernel_loss": record["kernel_loss"], "features": reconstructed, "feature_schema_version": SCHEMA,
                   "capture_context": {k: started[k] for k in ("capture_interface", "interface_index", "filter", "promiscuous")} | {
                       "local_addresses": record["local_addresses"], "flow_schema_version": record["schema_version"]},
                   "flow_count": len(flows), "unknown_packets": 0, "unknown_bytes": 0, "other_packets": 0})
    for name in ("packets", "ip_bytes", "outbound_packets", "outbound_bytes", "inbound_packets", "inbound_bytes"):
        window[name] = sum(getattr(f, name) for f in flows.values())
    for protocol in ("TCP", "UDP"):
        window[protocol.lower() + "_packets"] = sum(f.packets for k, f in flows.items() if k[1] == protocol)
    eligible(window)
    profile(session, window)
    return {"session": session, "window": window}


def export(paths, source_id, observation_profile, mode="LIVE"):
    """Streaming input with explicit exclusions. Export never certifies benign traffic."""
    UUID(source_id)
    rows, exclusions, sources, starts, identities = [], Counter(), [], {}, set()
    total_bytes = 0
    for name in paths:
        path = Path(name)
        total_bytes += path.stat().st_size
        if total_bytes > 256 * 1024 * 1024:
            raise ValueError("Raw evidence exceeds 256 MiB export budget")
        raw = path.read_bytes()
        sources.append({"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        encoding = "utf-16" if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else "utf-8-sig"
        for line in raw.decode(encoding).splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("nonobject_record")
                kind = record.get("type")
                if kind in ("capture_started", "capture_restarted"):
                    identity = record["session_id"]
                    if identity in starts and starts[identity] != record:
                        raise ValueError("conflicting_capture_start")
                    starts[identity] = record
                    continue
                if kind != "window":
                    continue
                if record.get("mode") != mode:
                    exclusions["different_mode"] += 1
                    continue
                if record.get("session_id") not in starts:
                    exclusions["missing_capture_start_context"] += 1
                    continue
                row = convert(record, starts[record["session_id"]], source_id, observation_profile)
                key = (record["session_id"], record["start"])
                if key in identities:
                    exclusions["duplicate_window"] += 1
                    continue
                identities.add(key)
                rows.append(row)
                if len(rows) > 20000:
                    raise OverflowError("Export exceeds 20000-window budget")
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                # Fixed reason categories avoid copying private addresses/raw records to reports.
                reason = str(exc) if isinstance(exc, ValueError) and str(exc).replace('_', '').isalnum() else "malformed_or_missing_metadata"
                exclusions[reason] += 1
    return {"schema": "netsentinel-dataset-v1", "feature_order": list(FEATURE_NAMES), "rows": rows,
            "export": {"eligible": len(rows), "excluded": dict(exclusions), "sources": sources,
                       "reviewed_normal": False, "source_id_origin": "operator_supplied", "observation_profile_origin": "operator_supplied"}}
