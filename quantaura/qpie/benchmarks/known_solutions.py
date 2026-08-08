"""Benchmarks against known identities + v0.5 suites."""

from __future__ import annotations

from typing import Any
import numpy as np

from quantaura.qpie.gauge import LatticeGaugeU1
from quantaura.qpie.vortex import helicity_3d
from quantaura.qpie.firewall import classify_candidate, DiscoveryTier, assert_not_new_physics
from quantaura.qpie.dec.complex2d import GridComplex2D, conservation_report
from quantaura.qpie.topology import topology_validation_suite
from quantaura.qpie.benchmarks.refinement import skyrmion_q_vs_resolution
from quantaura.qpie.adapters.tensor_network import cross_validate_ed_tn


def test_plaquette_identity_flat() -> dict[str, Any]:
    g = LatticeGaugeU1.zeros(8, 8)
    phase = g.plaquette_phase()
    action = g.wilson_action(1.0)
    ok = bool(np.allclose(phase, 0.0) and abs(action) < 1e-12)
    return {"name": "plaquette_identity_flat", "passed": ok, "wilson_action": action}


def test_helicity_zero_potential_flow() -> dict[str, Any]:
    n = 12
    v = np.zeros((n, n, n, 3))
    v[..., 0] = 1.0
    report = helicity_3d(v, dx=1.0)
    ok = abs(report.helicity) < 1e-8
    return {"name": "helicity_zero_potential_flow", "passed": ok, "helicity": report.helicity}


def test_firewall_blocks_tier5() -> dict[str, Any]:
    v = classify_candidate(
        residual=1e-8, matches_known_solution=False, reproduced_across_backends=3, has_lab_measurement=True
    )
    blocked = v.blocks_claim and v.tier < DiscoveryTier.POTENTIAL_NEW_LAW
    try:
        assert_not_new_physics(v)
        auto_ok = True
    except RuntimeError:
        auto_ok = False
    return {"name": "firewall_blocks_tier5", "passed": blocked and auto_ok, "tier": int(v.tier)}


def test_dec_conservation() -> dict[str, Any]:
    rep = conservation_report(GridComplex2D(7, 5))
    return {"name": "dec_conservation", **rep}


def run_all_benchmarks() -> list[dict[str, Any]]:
    results = [
        test_plaquette_identity_flat(),
        test_helicity_zero_potential_flow(),
        test_firewall_blocks_tier5(),
        test_dec_conservation(),
    ]
    results.extend(topology_validation_suite())
    results.append(skyrmion_q_vs_resolution([16, 24, 32, 48]))
    try:
        results.append(cross_validate_ed_tn(4))
    except Exception as exc:  # pragma: no cover
        results.append({"name": "ed_vs_tn_cross_validate", "passed": False, "error": str(exc)})
    try:
        from quantaura.qpie.schwinger.hamiltonian import cross_validate_dense_sparse

        results.append(cross_validate_dense_sparse(4))
    except Exception as exc:  # pragma: no cover
        results.append({"name": "dense_vs_sparse_ground", "passed": False, "error": str(exc)})
    return results
