"""Classical computing adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantaura.qpie.gauge import LatticeGaugeU1


@dataclass
class ClassicalAdapter:
    name: str = "classical"

    def wilson_scan(self, nx: int = 8, ny: int = 8, betas: list[float] | None = None) -> list[dict[str, Any]]:
        return run_gauge_wilson_scan(nx, ny, betas)


def run_gauge_wilson_scan(
    nx: int = 8,
    ny: int = 8,
    betas: list[float] | None = None,
    seed: int = 0,
) -> list[dict[str, Any]]:
    betas = betas or [0.5, 1.0, 2.0]
    gauge = LatticeGaugeU1.random(nx, ny, scale=0.2, seed=seed)
    out = []
    for b in betas:
        out.append(
            {
                "beta": b,
                "wilson_action": gauge.wilson_action(b),
                "mean_field_strength": gauge.mean_field_strength(),
                "backend": "classical",
            }
        )
    return out
