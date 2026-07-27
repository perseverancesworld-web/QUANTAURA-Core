"""Mathematical & entropy-based model primitives."""

from __future__ import annotations

from typing import Sequence
import math


def shannon_entropy(probabilities: Sequence[float]) -> float:
    h = 0.0
    for p in probabilities:
        if p > 0:
            h -= p * math.log2(p)
    return h


def normalize(values: Sequence[float]) -> list[float]:
    total = sum(values)
    if total == 0:
        return [0.0] * len(values)
    return [v / total for v in values]


def kl_divergence(p: Sequence[float], q: Sequence[float]) -> float:
    if len(p) != len(q):
        raise ValueError("Distributions must have the same length")
    div = 0.0
    for pi, qi in zip(p, q):
        if pi > 0 and qi > 0:
            div += pi * math.log2(pi / qi)
    return div


def fractal_dimension_boxcount(
    points: Sequence[tuple[float, float]],
    box_sizes: Sequence[float] | None = None,
) -> float:
    if not points:
        return 0.0

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    if box_sizes is None:
        span = max(max_x - min_x, max_y - min_y) or 1.0
        box_sizes = [span / (2 ** k) for k in range(1, 6)]

    counts = []
    for size in box_sizes:
        if size <= 0:
            continue
        boxes: set[tuple[int, int]] = set()
        for x, y in points:
            bx = int((x - min_x) / size)
            by = int((y - min_y) / size)
            boxes.add((bx, by))
        counts.append(len(boxes))

    if len(counts) < 2:
        return 0.0

    log_inv_size = [math.log(1.0 / s) for s in box_sizes[: len(counts)]]
    log_n = [math.log(c) if c > 0 else 0.0 for c in counts]

    n = len(log_n)
    mean_x = sum(log_inv_size) / n
    mean_y = sum(log_n) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_inv_size, log_n))
    den = sum((x - mean_x) ** 2 for x in log_inv_size)
    return num / den if den != 0 else 0.0
