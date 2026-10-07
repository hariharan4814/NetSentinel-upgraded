"""Seeded metadata generation. No sockets, capture libraries or network I/O."""
import hashlib
import random

from sensor.features import FEATURE_NAMES, host_features
from sensor.flows import WindowAggregator
from sensor.models import PacketMetadata
from .contracts import (BENIGN, FAMILIES, GENERATOR_VERSION, MAX_EVENTS,
                        MAX_EVENTS_PER_WINDOW, MODE, check_cancel, digest,
                        validate_config)

LOCAL_IP = "192.0.2.1"
INTERFACE = "virtual-metadata"
EPOCH = 1_735_689_600  # 2025-01-01 UTC, fixed virtual clock; not capture time.


def run_seed(seed, family, index):
    return int.from_bytes(hashlib.sha256(f"{seed}:{family}:{index}".encode()).digest()[:8], "big")


def split_runs(config):
    """Assign independent whole runs before any window is generated."""
    count = config["runs_per_family"]
    train_count, validation_count = int(count * 0.6), max(1, int(count * 0.2))
    runs = []
    for family in FAMILIES:
        for index in range(count):
            split = "train" if index < train_count else (
                "validation" if index < train_count + validation_count else "test")
            runs.append({"id": f"{family}-{index:03d}", "family": family,
                         "seed": run_seed(config["seed"], family, index), "split": split})
    return runs


def packet_window(rng, family, start, config, run_scale=1.0):
    """Return payload-free metadata and the *injected* window family.

    Families overlap deliberately: background media, discovery and legitimate
    bulk workloads can resemble challenges. Intensity changes counts, never
    labels or arbitrary model scores. Sparse/idle windows are genuine observed
    simulation windows. Missing observation is handled separately by generate.
    """
    active = family
    if family not in BENIGN and rng.random() < 0.25:
        active = "routine"
    if active in BENIGN and rng.random() < 0.06:
        return [], "routine"
    # Noise mixes a background packet distribution without changing its role.
    style = active
    if rng.random() < config["noise"]:
        style = rng.choice(FAMILIES)
    profiles = {
        "routine": (45, 0.35, 0.18, 0.10, 6, 650),
        "bulk_transfer": (180, 0.45, 0.15, 0.03, 5, 1100),
        "fanout": (115, 0.83, 0.15, 0.45, 40, 140),
        "syn_burst": (205, 0.80, 0.04, 0.83, 9, 95),
        "udp_burst": (205, 0.70, 0.91, 0.04, 10, 680),
    }
    mean_count, outbound, udp, syn, peers, size = profiles[style]
    # Continuous overlapping run/window variability; no seed/case identifiers
    # appear among features. The bound defines workload size, not downsampling.
    count = int(mean_count * run_scale * rng.uniform(0.35, 1.5) * config["intensity"])
    count = max(1, min(MAX_EVENTS_PER_WINDOW, count))
    peer_count = max(1, min(100, int(peers * rng.uniform(0.3, 1.8))))
    outbound = min(0.98, max(0.02, outbound + rng.uniform(-0.25, 0.25)))
    udp = min(1.0, max(0.0, udp + rng.uniform(-0.18, 0.18)))
    syn = min(1.0, max(0.0, syn + rng.uniform(-0.20, 0.20)))
    times = sorted(rng.uniform(0.001, 9.999) for _ in range(count))
    packets = []
    for offset in times:
        remote = f"198.51.100.{rng.randint(1, peer_count)}"
        is_outbound = rng.random() < outbound
        protocol = "UDP" if rng.random() < udp else "TCP"
        length = max(40, min(1500, int(rng.gauss(size, max(30, size * 0.35)))))
        remote_port = rng.choice((53, 80, 443, 8080, 8443))
        if style == "fanout":
            remote_port = rng.randint(1, 65535)
        packets.append(PacketMetadata(
            timestamp=start + offset, interface=INTERFACE,
            source_ip=LOCAL_IP if is_outbound else remote,
            destination_ip=remote if is_outbound else LOCAL_IP,
            source_port=49000 if is_outbound else remote_port,
            destination_port=remote_port if is_outbound else 49000,
            protocol=protocol, packet_length=length,
            direction="outbound" if is_outbound else "inbound",
            tcp_syn=rng.random() < syn if protocol == "TCP" else None))
    return packets, active


def aggregate_packets(packets, *, start, run_id, missing=False):
    """Use the unchanged sensor aggregator and frozen host-v1 formulas."""
    aggregator = WindowAggregator(start=start, mode=MODE, session_id=run_id,
                                  interface=INTERFACE, max_flows=1024)
    for packet in packets:
        aggregator.advance(packet.timestamp)
        if not aggregator.add(packet):
            raise ValueError("simulation flow budget exceeded")
    if missing:
        aggregator.mark_loss()
    finalized = aggregator.advance(start + 12)
    if len(finalized) != 1:
        raise ValueError("expected one complete ten-second virtual window")
    return host_features(finalized[0], {LOCAL_IP})


def generate_dataset(config, *, progress=None, cancelled=None):
    config = validate_config(config)
    runs = split_runs(config)
    total = len(runs) * config["windows_per_run"]
    samples, truth, events = [], {}, 0
    splits = {name: {"run_ids": [], "windows": 0} for name in ("train", "validation", "test")}
    for run in runs:
        check_cancel(cancelled)
        splits[run["split"]]["run_ids"].append(run["id"])
        rng = random.Random(run["seed"])
        # Independent stream for observation gaps: changing gap probability
        # does not silently change traffic in the remaining windows.
        gap_rng = random.Random(run["seed"] ^ 0x6A09E667)
        scale = rng.uniform(0.65, 1.35)
        for index in range(config["windows_per_run"]):
            check_cancel(cancelled)
            start = EPOCH + index * 10
            packets, family = packet_window(rng, run["family"], start, config, scale)
            events += len(packets)
            if events > MAX_EVENTS:
                raise ValueError("generated event budget exceeded; reduce runs, duration or intensity")
            missing = gap_rng.random() < config["gap_probability"]
            features = aggregate_packets(packets, start=start, run_id=run["id"], missing=missing)
            sample_id = f"{run['id']}-w{index:04d}"
            samples.append({"id": sample_id, "run_id": run["id"], "window_index": index,
                            "time_seconds": index * 10, "features": features,
                            "event_count": len(packets), "observed": not missing})
            truth[sample_id] = {"family": family, "challenge": family not in BENIGN}
            splits[run["split"]]["windows"] += 1
            if progress and (len(samples) % 10 == 0 or len(samples) == total):
                progress("generating", len(samples), total)
    data = {"schema_version": "lab-dataset-v1", "mode": MODE,
            "generator_version": GENERATOR_VERSION, "config": config,
            "feature_names": list(FEATURE_NAMES), "runs": runs,
            "splits": splits, "samples": samples, "truth": truth, "event_count": events}
    data["sha256"] = digest(data)
    return data
