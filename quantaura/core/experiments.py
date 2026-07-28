"""Experiment config loader and runner for nested simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid

from quantaura.core.simulation import SimulationEngine, simple_growth_step, nested_market_step

_STEP_FNS = {
    "growth": simple_growth_step,
    "market": nested_market_step,
}


@dataclass
class ExperimentConfig:
    name: str
    model: str = "growth"
    initial_state: dict[str, Any] = field(default_factory=dict)
    n_steps: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)
    nested: list["ExperimentConfig"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        nested = [cls.from_dict(n) for n in data.get("nested", [])]
        return cls(
            name=data.get("name", "unnamed"),
            model=data.get("model", "growth"),
            initial_state=data.get("initial_state", {}),
            n_steps=int(data.get("n_steps", 10)),
            metadata=data.get("metadata", {}),
            nested=nested,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "ExperimentConfig":
        text = Path(path).read_text()
        data = json.loads(text)
        return cls.from_dict(data)


@dataclass
class ExperimentResult:
    experiment_id: str
    name: str
    final_state: dict[str, Any]
    step_count: int
    nested_results: list["ExperimentResult"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    step_fn = _STEP_FNS.get(config.model)
    if not step_fn:
        raise ValueError(f"Unknown model: {config.model}")

    defaults = {
        "growth": {"population": 100.0, "growth_rate": 0.05},
        "market": {"price": 100.0, "volatility": 0.01, "regime": "calm"},
    }
    state = {**defaults.get(config.model, {}), **config.initial_state}
    engine = SimulationEngine(config.name)
    sim = engine.run(state, step_fn, n_steps=config.n_steps, metadata=config.metadata)

    nested_results = [run_experiment(n) for n in config.nested]

    return ExperimentResult(
        experiment_id=f"exp_{uuid.uuid4().hex[:10]}",
        name=config.name,
        final_state=sim.final_state,
        step_count=len(sim.steps),
        nested_results=nested_results,
        metadata=config.metadata,
    )
