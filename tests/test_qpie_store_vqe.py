from quantaura.qpie.store.sqlite_registry import SQLiteHypothesisStore
from quantaura.qpie.hypothesis import Hypothesis, Anomaly
from quantaura.qpie.adapters.vqe import classical_variational_stub
from fastapi.testclient import TestClient
from quantaura.api.main import app


def test_sqlite_hypothesis_roundtrip():
    s = SQLiteHypothesisStore(":memory:")
    h = Hypothesis.create("test statement", predicted_observables=["gap"])
    s.save_hypothesis(h)
    assert s.get_hypothesis(h.hypothesis_id)["statement"] == "test statement"
    a = Anomaly.create("odd residual", solver="ed")
    s.save_anomaly(a)
    assert len(s.list_anomalies()) == 1


def test_vqe_stub_reports_ed():
    r = classical_variational_stub(3, n_samples=5, seed=1)
    assert r.reference_ed_ground is not None
    assert r.abs_error_vs_ed is not None


def test_api_vqe_and_anomaly():
    client = TestClient(app)
    r = client.post("/v1/qpie/vqe/stub", json={"n_sites": 3, "n_samples": 5})
    assert r.status_code == 200
    assert "reference_ed_ground" in r.json()
    a = client.post("/v1/qpie/anomalies", json={"description": "test anomaly", "solver": "ed"})
    assert a.status_code == 200
    listed = client.get("/v1/qpie/anomalies")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
