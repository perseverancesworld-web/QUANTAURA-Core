import numpy as np
from fastapi.testclient import TestClient

from quantaura.api.main import app
from quantaura.qpie.dec.complex2d import GridComplex2D, discrete_gradient, discrete_curl
from quantaura.qpie.schwinger.hamiltonian import exact_spectrum, build_schwinger_like_matrix
from quantaura.qpie.telemetry.manifest import ExperimentManifest, SensorReading, new_run_id, pair_sim_and_measure
from quantaura.qpie.hypothesis import Hypothesis, HypothesisRegistry
from quantaura.qpie.active import ExperimentCandidate, select_next_experiment
from quantaura.qpie.validation import compare_solvers
from quantaura.qpie.gauge import LatticeGaugeU1


def test_d2_equals_zero():
    c = GridComplex2D(5, 7)
    d0, d1 = c.incidence_d0(), c.incidence_d1()
    assert np.allclose(d1 @ d0, 0.0)


def test_gradient_curl_composition():
    c = GridComplex2D(4, 4)
    rng = np.random.default_rng(0)
    f = rng.standard_normal(c.n0)
    assert np.allclose(discrete_curl(c, discrete_gradient(c, f)), 0.0, atol=1e-10)


def test_schwinger_hermitian_spectrum():
    H = build_schwinger_like_matrix(3, m=0.2, h=0.05)
    assert np.allclose(H, H.conj().T)
    rep = exact_spectrum(3, m=0.2, h=0.05)
    assert len(rep.eigenvalues) == 8


def test_manifest_pair():
    m = ExperimentManifest(run_id=new_run_id(), title="t", solver="ed")
    m.simulation_outputs["energy"] = -1.5
    m.add_measurement(SensorReading("s1", "energy", -1.48, uncertainty=0.02))
    assert pair_sim_and_measure(m, "energy", "energy")["n_measurements"] == 1


def test_hypothesis_registry():
    reg = HypothesisRegistry()
    h = Hypothesis.create("Gap closes at critical m")
    reg.register(h)
    assert reg.get(h.hypothesis_id) is not None


def test_active_selection():
    best = select_next_experiment(
        [
            ExperimentCandidate("a", expected_info_gain=1.0, cost=10.0),
            ExperimentCandidate("b", expected_info_gain=0.5, cost=0.1),
        ]
    )
    assert best is not None and best.experiment_id == "b"


def test_cross_solver_flat_gauge():
    def a():
        return LatticeGaugeU1.zeros(4, 4).wilson_action()

    def b():
        return float(np.sum(1.0 - np.real(LatticeGaugeU1.zeros(4, 4).plaquette_holonomy())))

    r = compare_solvers("flat_wilson", a, b, lambda: 0.0, tol=1e-12)
    assert r.agreed


def test_api_qpie_benchmarks():
    client = TestClient(app)
    r = client.get("/v1/qpie/benchmarks")
    assert r.status_code == 200 and r.json()["all_passed"] is True


def test_api_schwinger():
    client = TestClient(app)
    r = client.post("/v1/qpie/schwinger/spectrum", json={"n_sites": 3, "m": 0.5, "h": 0.1})
    assert r.status_code == 200 and "gap" in r.json()


def test_api_dec_status():
    client = TestClient(app)
    r = client.get("/v1/qpie/dec/status")
    assert r.status_code == 200 and r.json()["d2_is_zero"] is True
