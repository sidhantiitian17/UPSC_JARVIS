from __future__ import annotations

import math
from collections import Counter


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (no interpolation)."""
    if not values:
        raise ValueError("no values")
    xs = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(xs))) if pct > 0 else 1
    return xs[min(rank, len(xs)) - 1]


def summarize_latency(seconds: list[float]) -> dict:
    if not seconds:
        raise ValueError("no latency samples")
    ms = [s * 1000 for s in seconds]
    return {"n": len(ms), "p50_ms": percentile(ms, 50), "p95_ms": percentile(ms, 95),
            "max_ms": max(ms), "mean_ms": sum(ms) / len(ms)}


def accuracy(pred: list[str], gold: list[str]) -> float:
    if len(pred) != len(gold):
        raise ValueError("length mismatch")
    if not gold:
        raise ValueError("empty")
    return sum(p == g for p, g in zip(pred, gold, strict=True)) / len(gold)


def majority_baseline(gold: list[str]) -> float:
    return Counter(gold).most_common(1)[0][1] / len(gold)
