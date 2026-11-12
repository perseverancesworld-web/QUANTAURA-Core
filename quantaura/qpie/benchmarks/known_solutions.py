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




def test_rhythmic_energy_balance() -> dict[str, Any]:
    from quantaura.qpie.rhythm import simulate_rhythmic_network

    result = simulate_rhythmic_network(
        mass=np.array([1.0]),
        damping=np.array([0.15]),
        stiffness=np.array([4.0]),
        initial_position=np.array([0.0]),
        initial_velocity=np.array([0.0]),
        dt=0.001,
        steps=4000,
        drive=lambda t: np.array([np.sin(2.0 * t)]),
    )
    residual = result.max_abs_energy_balance_residual
    return {
        "name": "rhythmic_energy_balance",
        "passed": bool(residual < 1e-4),
        "energy_balance_residual": residual,
        "input_work": float(result.cumulative_input_work[-1]),
        "dissipation": float(result.cumulative_dissipation[-1]),
    }


def test_spectral_gauge_invariance() -> dict[str, Any]:
    from quantaura.qpie.spectral import (
        gauge_covariant_hamiltonian,
        gauge_transform,
        hermitian_spectrum,
    )

    gauge = LatticeGaugeU1.random(4, 5, scale=0.25, seed=27)
    alpha = np.random.default_rng(28).uniform(-np.pi, np.pi, size=(4, 5))
    e0 = hermitian_spectrum(gauge_covariant_hamiltonian(gauge)).eigenvalues
    e1 = hermitian_spectrum(
        gauge_covariant_hamiltonian(gauge_transform(gauge, alpha))
    ).eigenvalues
    residual = float(np.max(np.abs(e0 - e1)))
    return {
        "name": "spectral_gauge_invariance",
        "passed": bool(residual < 1e-10),
        "spectrum_residual": residual,
    }



def test_uniform_flux_torus() -> dict[str, Any]:
    from quantaura.qpie.spectral import (
        principal_plaquette_phase,
        uniform_flux_gauge,
    )

    fluxes = (0.0, np.pi / 6.0, np.pi / 3.0, np.pi / 2.0)
    residuals = []
    for flux in fluxes:
        gauge = uniform_flux_gauge(12, 12, flux)
        residuals.append(
            float(np.max(np.abs(principal_plaquette_phase(gauge) - flux)))
        )
    residual = max(residuals, default=0.0)
    return {
        "name": "sth1_uniform_flux_torus",
        "passed": bool(residual < 1e-10),
        "max_plaquette_residual": residual,
        "fluxes": [float(v) for v in fluxes],
    }

def run_all_benchmarks() -> list[dict[str, Any]]:
    results = [
        test_plaquette_identity_flat(),
        test_helicity_zero_potential_flow(),
        test_firewall_blocks_tier5(),
        test_dec_conservation(),
    ]
    results.extend(topology_validation_suite())
    results.append(test_rhythmic_energy_balance())
    results.append(test_spectral_gauge_invariance())
    results.append(test_uniform_flux_torus())
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
