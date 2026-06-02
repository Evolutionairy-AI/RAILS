"""Statistics helpers for the experiments."""
from __future__ import annotations
import math


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (better than normal at the
    tails and for small n). Returns (low, high), clamped to [0, 1]."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def median(xs: list[float]):
    if not xs:
        return None
    s = sorted(xs)
    return s[len(s) // 2]
