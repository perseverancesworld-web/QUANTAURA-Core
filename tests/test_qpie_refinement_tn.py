from fastapi.testclient import TestClient

from quantaura.api.main import app
from quantaura.qpie.benchmarks.refinement import skyrmion_q_vs_resolution
from quantaura.qpie.adapters.tensor_network import (
    ExactTNProxy,
    TruncatedSubspaceProxy,
    cross_validate_ed_tn,
    cross_validate_sparse_tn,
)
from quantaura.qpie.benchmarks.known_solutions import run_all_benchmarks


def test_refinement_improves():
    r = skyrmion_q_vs_resolution([16, 32, 48])
    assert r["passed"], r
    assert r["finest_err"] < 0.25


def test_tn_proxy_matches_ed():
    r = cross_validate_ed_tn(4)
    assert r["passed"], r


def test_sparse_tn():
    assert cross_validate_sparse_tn(4)["passed"]


def test_truncated_is_upper_bound():
    t = TruncatedSubspaceProxy().spectrum(3, bond_dim=4)
    e = ExactTNProxy().spectrum(3)
    assert t.ground_energy >= e.ground_energy - 1e-6


def test_benchmarks_include_new():
    names = {x["name"] for x in run_all_benchmarks()}
    assert "skyrmion_q_refinement" in names
    assert "ed_vs_tn_cross_validate" in names


def test_api_refinement_tn():
    client = TestClient(app)
    r = client.get("/v1/qpie/topology/refinement")
    assert r.status_code == 200
    assert r.json()["passed"] is True
    t = client.get("/v1/qpie/tn/cross_validate?n_sites=3")
    assert t.status_code == 200 and t.json()["passed"] is True
