"""Tests for research API endpoints."""

from fastapi.testclient import TestClient

from quantaura.api.main import app

client = TestClient(app)


def test_simulate_growth():
    resp = client.post(
        "/v1/research/simulate",
        json={"model": "growth", "n_steps": 5, "initial_state": {"population": 100.0}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_state"]["population"] > 100.0
    assert data["step_count"] == 6


def test_cognitive_summary():
    resp = client.get("/v1/research/cognitive/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_count"] >= 7


def test_entropy():
    resp = client.post("/v1/research/entropy", json={"probabilities": [0.5, 0.5]})
    assert resp.status_code == 200
    assert abs(resp.json()["entropy_bits"] - 1.0) < 1e-6


def test_momentum():
    resp = client.post(
        "/v1/research/momentum",
        json={"prices": [100, 102, 101, 105, 110, 108, 112], "lookback": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "momentum" in data
    assert "sma" in data
