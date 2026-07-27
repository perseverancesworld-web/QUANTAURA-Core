"""Minimal multi-scale simulation engine (Fractal Intelligence scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import time
import uuid


@dataclass
class SimulationStep:
    step: int
    state: dict[str, Any]
    timestamp: float


@dataclass
class SimulationResult:
    sim_id: str
    steps: list[SimulationStep] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class SimulationEngine:
    """Simple discrete-time simulation runner."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self.history: list[SimulationResult] = []

    def run(
        self,
        initial_state: dict[str, Any],
        step_fn: Callable[[dict[str, Any], int], dict[str, Any]],
        n_steps: int = 10,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SimulationResult:
        sim_id = f"sim_{uuid.uuid4().hex[:10]}"
        state = dict(initial_state)
        steps: list[SimulationStep] = [
            SimulationStep(step=0, state=dict(state), timestamp=time.time())
        ]

        for i in range(1, n_steps + 1):
            state = step_fn(state, i)
            steps.append(
                SimulationStep(step=i, state=dict(state), timestamp=time.time())
            )

        result = SimulationResult(
            sim_id=sim_id,
            steps=steps,
            final_state=state,
            metadata=metadata or {"engine": self.name},
        )
        self.history.append(result)
        return result


def simple_growth_step(state: dict[str, Any], step: int) -> dict[str, Any]:
    population = state.get("population", 1.0)
    rate = state.get("growth_rate", 0.05)
    return {
        **state,
        "population": population * (1 + rate),
        "step": step,
    }


def nested_market_step(state: dict[str, Any], step: int) -> dict[str, Any]:
    price = state.get("price", 100.0)
    vol = state.get("volatility", 0.01)
    regime = state.get("regime", "calm")

    if step % 7 == 0:
        regime = "volatile" if regime == "calm" else "calm"
        vol = 0.05 if regime == "volatile" else 0.01

    import random
    shock = random.gauss(0, vol)
    new_price = price * (1 + shock)

    return {
        **state,
        "price": new_price,
        "volatility": vol,
        "regime": regime,
        "step": step,
    }
