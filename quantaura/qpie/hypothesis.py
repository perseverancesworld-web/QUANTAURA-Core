"""Hypothesis registry and anomaly objects."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import time
import uuid


@dataclass
class Hypothesis:
    hypothesis_id: str
    statement: str
    assumptions: list[str] = field(default_factory=list)
    predicted_observables: list[str] = field(default_factory=list)
    falsification_criteria: list[str] = field(default_factory=list)
    supporting_runs: list[str] = field(default_factory=list)
    contradictory_runs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(cls, statement: str, **kwargs: Any) -> "Hypothesis":
        return cls(hypothesis_id=f"H_{uuid.uuid4().hex[:10]}", statement=statement, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HypothesisRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Hypothesis] = {}

    def register(self, h: Hypothesis) -> str:
        self._items[h.hypothesis_id] = h
        return h.hypothesis_id

    def get(self, hid: str) -> Optional[Hypothesis]:
        return self._items.get(hid)

    def list(self) -> list[dict[str, Any]]:
        return [h.to_dict() for h in self._items.values()]


@dataclass
class Anomaly:
    anomaly_id: str
    description: str
    hypothesis_id: str = ""
    model_version: str = ""
    solver: str = ""
    discretization: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    benchmark_status: str = "open"
    conservation_residuals: dict[str, float] = field(default_factory=dict)
    independent_replication: list[str] = field(default_factory=list)
    experimental_evidence: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, description: str, **kwargs: Any) -> "Anomaly":
        return cls(anomaly_id=f"A_{uuid.uuid4().hex[:10]}", description=description, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
