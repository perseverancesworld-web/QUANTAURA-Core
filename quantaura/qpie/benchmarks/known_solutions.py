"""Benchmarks against known identities (calibration laboratories)."""

from __future__ import annotations

from typing import Any
import numpy as np

from quantaura.qpie.gauge import LatticeGaugeU1
from quantaura.qpie.vortex import helicity_3d
from quantaura.qpie.firewall import classify_candidate, DiscoveryTier, assert_not_new_physics


def test_plaquette_identity_flat() -> dict[str, Any]:
    g = LatticeGaugeU1.zeros(8, 8)
    phase = g.plaquette_phase()
    action = g.wilson_action(1.0)
    ok = bool(np.allclose(phase, 0.0) and abs(action) < 1e-12)
    return {
        "name": "plaquette_identity_flat",
        "passed": ok,
        "max_abs_phase": float(np.max(np.abs(phase))),
        "wilson_action": action,
    }


def test_helicity_zero_potential_flow() -> dict[str, Any]:
    n = 12
    v = np.zeros((n, n, n, 3))
    v[..., 0] = 1.0
    report = helicity_3d(v, dx=1.0)
    ok = abs(report.helicity) < 1e-8 and report.mean_vorticity_norm < 1e-8
    return {
        "name": "helicity_zero_potential_flow",
        "passed": ok,
        "helicity": report.helicity,
        "mean_vorticity": report.mean_vorticity_norm,
    }


def test_firewall_blocks_tier5() -> dict[str, Any]:
    v = classify_candidate(
        residual=1e-8,
        matches_known_solution=False,
        reproduced_across_backends=3,
        has_lab_measurement=True,
    )
    blocked = v.blocks_claim and v.tier < DiscoveryTier.POTENTIAL_NEW_LAW
    try:
        assert_not_new_physics(v)
        auto_ok = True
    except RuntimeError:
        auto_ok = False
    return {
        "name": "firewall_blocks_tier5",
        "passed": blocked and auto_ok and v.tier == DiscoveryTier.ROBUST_UNEXPLAINED,
        "tier": int(v.tier),
        "label": v.label,
    }


def run_all_benchmarks() -> list[dict[str, Any]]:
    return [
        test_plaquette_identity_flat(),
        test_helicity_zero_potential_flow(),
        test_firewall_blocks_tier5(),
    ]
