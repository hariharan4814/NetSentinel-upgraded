"""Actual OS counters, monotonic rates, and explicit invalid intervals."""
from dataclasses import asdict, dataclass
import math
import psutil
from .interfaces import InterfaceUnavailable


@dataclass(frozen=True, slots=True)
class Counters:
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int


def read_counters(interface: str) -> Counters:
    raw = psutil.net_io_counters(pernic=True, nowrap=False).get(interface)
    if raw is None:
        raise InterfaceUnavailable(f"OS counters unavailable for {interface!r}")
    return Counters(raw.bytes_sent, raw.bytes_recv, raw.packets_sent, raw.packets_recv)


def calculate_rates(before: Counters, after: Counters, elapsed: float) -> dict:
    if not math.isfinite(elapsed) or elapsed <= 0:
        raise ValueError("elapsed must be positive and finite")
    delta = {key: value - asdict(before)[key] for key, value in asdict(after).items()}
    reason = "counter_reset" if any(v < 0 for v in delta.values()) else (
        "sampling_gap" if elapsed > 3 else None)
    return {"elapsed_seconds": elapsed, "valid": reason is None, "reason": reason,
            "delta": None if reason else delta,
            "upload_bytes_per_second": None if reason else delta["bytes_sent"] / elapsed,
            "download_bytes_per_second": None if reason else delta["bytes_received"] / elapsed}
