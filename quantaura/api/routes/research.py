"""Research OS endpoints — simulation, cognitive architecture, quant helpers.

These expose the core research primitives over HTTP so agents and notebooks
can drive experiments without importing the library directly.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from quantaura.core.simulation import SimulationEngine, simple_growth_step, nested_market_step
from quantaura.core.cognitive import build_default_architecture
from quantaura.core.math_models import shannon_entropy, normalize
from quantaura.core.quant import simple_moving_average, sharpe_ratio, momentum_signal

router = APIRouter(prefix="/v1/research", tags=["Research"])

_STEP_FNS = {
    "growth": simple_growth_step,
    "market": nested_market_step,
}


class SimulationRequest(BaseModel):
    model: str = Field("growth", description="growth | market")
    initial_state: dict[str, Any] = Field(default_factory=dict)
    n_steps: int = Field(10, ge=1, le=1000)


class EntropyRequest(BaseModel):
    probabilities: list[float]


class MomentumRequest(BaseModel):
    prices: list[float]
    lookback: int = 20


@router.post("/simulate")
def run_simulation(body: SimulationRequest) -> dict[str, Any]:
    step_fn = _STEP_FNS.get(body.model)
    if not step_fn:
        raise HTTPException(status_code=400, detail=f"Unknown model: {body.model}")

    defaults = {
        "growth": {"population": 100.0, "growth_rate": 0.05},
        "market": {"price": 100.0, "volatility": 0.01, "regime": "calm"},
    }
    state = {**defaults.get(body.model, {}), **body.initial_state}

    engine = SimulationEngine(body.model)
    result = engine.run(state, step_fn, n_steps=body.n_steps)
    return {
        "sim_id": result.sim_id,
        "model": body.model,
        "n_steps": body.n_steps,
        "final_state": result.final_state,
        "step_count": len(result.steps),
    }


@router.get("/cognitive/summary")
def cognitive_summary() -> dict[str, Any]:
    arch = build_default_architecture()
    return arch.summary()


@router.post("/entropy")
def compute_entropy(body: EntropyRequest) -> dict[str, float]:
    probs = normalize(body.probabilities)
    return {"entropy_bits": shannon_entropy(probs)}


@router.post("/momentum")
def compute_momentum(body: MomentumRequest) -> dict[str, Any]:
    if len(body.prices) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 prices")
    return {
        "momentum": momentum_signal(body.prices, lookback=body.lookback),
        "sma": simple_moving_average(body.prices, window=min(5, len(body.prices))),
        "returns_sharpe": sharpe_ratio(
            [(body.prices[i] / body.prices[i - 1]) - 1.0 for i in range(1, len(body.prices))]
        ),
    }
