"""QPIE-27 unit tests and known-solution benchmarks."""

import numpy as np

from quantaura.qpie import (
    LatticeGaugeU1,
    default_physics_graph,
    empty_lattice_state,
    helicity_3d,
    hopf_proxy_3d,
    classify_candidate,
    DiscoveryTier,
    run_all_benchmarks,
    score_experiment,
    default_metamaterial_seed,
    Observatory,
    PhysicalStateAgent,
)
from quantaura.qpie.adapters.classical import run_gauge_wilson_scan


def test_empty_state_summary():
    s = empty_lattice_state((8, 8))
    assert s.geometry["shape"] == (8, 8)
    assert "geometry_keys" in s.summary()


def test_gauge_flat_action_zero():
    g = LatticeGaugeU1.zeros(6, 6)
    assert abs(g.wilson_action()) < 1e-12


def test_gauge_random_finite():
    g = LatticeGaugeU1.random(6, 6, seed=1)
    assert g.wilson_action(1.0) > 0


def test_helicity_constant_flow():
    n = 8
    v = np.zeros((n, n, n, 3))
    v[..., 0] = 1.0
    r = helicity_3d(v)
    assert abs(r.helicity) < 1e-8


def test_hopf_proxy_runs():
    n = 6
    field = np.zeros((n, n, n, 3))
    field[..., 2] = 1.0
    rep = hopf_proxy_3d(field)
    assert isinstance(rep.hopf_proxy, float)


def test_causal_intervention():
    g = default_physics_graph()
    result = g.do("geometry", 2.0)
    assert "em" in result.observed_effects


def test_discovery_score():
    s = score_experiment(
        anomaly=1.0, information_gain=1.0, cross_domain=0.5, topological=0.2, cost=0.1, risk=0.1
    )
    assert s.value() > 0


def test_firewall_artifact():
    v = classify_candidate(residual=1.0, matches_known_solution=False, conservation_ok=False)
    assert v.tier == DiscoveryTier.ARTIFACT
    assert v.blocks_claim


def test_prism_seed():
    m = default_metamaterial_seed(8, 8)
    assert m.lattice is not None
    assert "epsilon" in m.lattice.fields


def test_observatory():
    obs = Observatory()
    a = PhysicalStateAgent.create(role="sensor", location="lab-1", temp=300.0)
    obs.register(a)
    assert obs.size() == 1
    assert len(obs.by_role("sensor")) == 1


def test_wilson_scan_adapter():
    rows = run_gauge_wilson_scan(4, 4, betas=[1.0])
    assert rows[0]["backend"] == "classical"


def test_known_solution_benchmarks():
    results = run_all_benchmarks()
    assert all(r["passed"] for r in results), results
