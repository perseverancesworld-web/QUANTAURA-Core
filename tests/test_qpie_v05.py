from fastapi.testclient import TestClient

from quantaura.api.main import app
from quantaura.qpie.dec import GridComplex2D, conservation_report
from quantaura.qpie.schwinger import cross_validate_dense_sparse
from quantaura.qpie.topology import baby_skyrmion_2d, skyrmion_density_2d, topology_validation_suite
from quantaura.qpie.ledger.scientific import ScientificLedger, EvidenceRecord
from quantaura.qpie.benchmarks.known_solutions import run_all_benchmarks


def test_dec_v2_conservation():
    assert conservation_report(GridComplex2D(6, 8))["passed"]


def test_sparse_matches_dense():
    r = cross_validate_dense_sparse(4)
    assert r["passed"], r


def test_baby_skyrmion_charge():
    _, q = skyrmion_density_2d(baby_skyrmion_2d(40, radius=7.0))
    assert abs(abs(q) - 1.0) < 0.3


def test_topology_uniform_passed():
    assert topology_validation_suite()[0]["passed"]


def test_scientific_ledger():
    led = ScientificLedger(":memory:")
    e = EvidenceRecord.create("benchmark", {"ok": True}, solver="test")
    led.append(e)
    assert led.list("benchmark")[0]["payload_hash"] == e.payload_hash


def test_benchmarks_include_dec():
    assert "dec_conservation" in {r["name"] for r in run_all_benchmarks()}


def test_qpie_routes_registered():
    """Use OpenAPI paths — APIRouter prefix is not always visible on route.path."""
    paths = set(app.openapi().get("paths", {}).keys())
    required = (
        "/v1/qpie/schwinger/sparse",
        "/v1/qpie/dec/conservation",
        "/v1/qpie/schwinger/cross_validate",
        "/v1/qpie/ledger/evidence",
        "/v1/qpie/topology/refinement",
        "/v1/qpie/tn/cross_validate",
    )
    missing = [p for p in required if p not in paths]
    assert not missing, f"missing OpenAPI paths {missing}; qpie={sorted(p for p in paths if p.startswith('/v1/qpie'))}"


def test_api_v05():
    client = TestClient(app)
    r = client.post("/v1/qpie/schwinger/sparse", json={"n_sites": 3})
    assert r.status_code == 200, r.text
    c = client.get("/v1/qpie/dec/conservation")
    assert c.status_code == 200 and c.json()["passed"] is True
    x = client.get("/v1/qpie/schwinger/cross_validate?n_sites=3")
    assert x.status_code == 200 and x.json()["passed"] is True
    assert client.get("/v1/qpie/ledger/evidence").status_code == 200
