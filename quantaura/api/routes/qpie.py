"""QPIE research HTTP surface — machine-readable experiment reports."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from quantaura.qpie.adapters.classical import run_gauge_wilson_scan
from quantaura.qpie.benchmarks.known_solutions import run_all_benchmarks
from quantaura.qpie.dec.complex2d import GridComplex2D
from quantaura.qpie.schwinger.hamiltonian import spectral_report
from quantaura.qpie.topology import hopf_proxy_3d
from quantaura.qpie.discovery import score_experiment
from quantaura.qpie.active import ExperimentCandidate, select_next_experiment
from quantaura.qpie.telemetry.manifest import ExperimentManifest, new_run_id
from quantaura.qpie.hypothesis import Hypothesis, HypothesisRegistry
import numpy as np

router = APIRouter(prefix="/v1/qpie", tags=["QPIE"])
_registry = HypothesisRegistry()


class WilsonRequest(BaseModel):
    nx: int = Field(8, ge=2, le=32)
    ny: int = Field(8, ge=2, le=32)
    betas: list[float] = Field(default_factory=lambda: [0.5, 1.0, 2.0])
    seed: int = 0


class SchwingerRequest(BaseModel):
    n_sites: int = Field(4, ge=2, le=10)
    m: float = 0.5
    h: float = 0.1


class DiscoveryScoreRequest(BaseModel):
    anomaly: float = 0.0
    information_gain: float = 0.0
    cross_domain: float = 0.0
    topological: float = 0.0
    cost: float = 0.1
    risk: float = 0.0


class ActiveSelectRequest(BaseModel):
    candidates: list[dict[str, Any]]
    lamb: float = 1.0


class HypothesisIn(BaseModel):
    statement: str
    assumptions: list[str] = Field(default_factory=list)
    predicted_observables: list[str] = Field(default_factory=list)
    falsification_criteria: list[str] = Field(default_factory=list)


@router.get("/benchmarks")
def qpie_benchmarks() -> dict[str, Any]:
    results = run_all_benchmarks()
    c = GridComplex2D(6, 6)
    d0, d1 = c.incidence_d0(), c.incidence_d1()
    residual = float(np.max(np.abs(d1 @ d0)))
    results.append({"name": "dec_d2_zero", "passed": residual < 1e-12, "max_abs_d1d0": residual})
    return {"run_id": new_run_id(), "results": results, "all_passed": all(r.get("passed", False) for r in results)}


@router.post("/gauge/wilson")
def qpie_wilson(body: WilsonRequest) -> dict[str, Any]:
    rows = run_gauge_wilson_scan(body.nx, body.ny, body.betas, seed=body.seed)
    return {"run_id": new_run_id(), "rows": rows}


@router.post("/schwinger/spectrum")
def qpie_schwinger(body: SchwingerRequest) -> dict[str, Any]:
    report = spectral_report(body.n_sites, body.m, body.h)
    report["run_id"] = new_run_id()
    return report


@router.get("/topology/hopf_proxy")
def qpie_hopf(n: int = 6) -> dict[str, Any]:
    if n < 2 or n > 24:
        raise HTTPException(400, "n out of range")
    field = np.zeros((n, n, n, 3))
    field[..., 2] = 1.0
    rep = hopf_proxy_3d(field)
    return {"run_id": new_run_id(), "hopf_proxy": rep.hopf_proxy, "mean_norm": rep.mean_norm, "energy_proxy": rep.energy_proxy, "notes": rep.notes}


@router.post("/discovery/score")
def qpie_discovery_score(body: DiscoveryScoreRequest) -> dict[str, Any]:
    s = score_experiment(
        anomaly=body.anomaly,
        information_gain=body.information_gain,
        cross_domain=body.cross_domain,
        topological=body.topological,
        cost=body.cost,
        risk=body.risk,
    )
    return {"run_id": new_run_id(), "score": s.value(), "components": s.__dict__}


@router.post("/discovery/select")
def qpie_select(body: ActiveSelectRequest) -> dict[str, Any]:
    cands = [
        ExperimentCandidate(
            experiment_id=c["experiment_id"],
            expected_info_gain=float(c["expected_info_gain"]),
            cost=float(c["cost"]),
            risk=float(c.get("risk", 0.0)),
        )
        for c in body.candidates
    ]
    best = select_next_experiment(cands, lamb=body.lamb)
    return {
        "run_id": new_run_id(),
        "selected": None
        if best is None
        else {
            "experiment_id": best.experiment_id,
            "score": best.score(body.lamb),
            "expected_info_gain": best.expected_info_gain,
            "cost": best.cost,
            "risk": best.risk,
        },
    }


@router.get("/dec/status")
def qpie_dec_status() -> dict[str, Any]:
    c = GridComplex2D(8, 8)
    d0, d1 = c.incidence_d0(), c.incidence_d1()
    residual = float(np.max(np.abs(d1 @ d0)))
    return {"run_id": new_run_id(), "n0": c.n0, "n1": c.n1, "n2": c.n2, "d2_residual": residual, "d2_is_zero": residual < 1e-12}


@router.post("/hypotheses")
def register_hypothesis(body: HypothesisIn) -> dict[str, Any]:
    h = Hypothesis.create(
        body.statement,
        assumptions=body.assumptions,
        predicted_observables=body.predicted_observables,
        falsification_criteria=body.falsification_criteria,
    )
    _registry.register(h)
    return h.to_dict()


@router.get("/hypotheses")
def list_hypotheses() -> list[dict[str, Any]]:
    return _registry.list()


@router.post("/telemetry/manifest")
def create_manifest(title: str = "untitled", solver: str = "classical") -> dict[str, Any]:
    m = ExperimentManifest(run_id=new_run_id(), title=title, solver=solver)
    return m.to_dict()
