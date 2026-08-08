"""Transition algebra: T:(S,I,C)->(S', Pi) with certificates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import time
import uuid


@dataclass
class Certificate:
    energy: Optional[float] = None
    topological_charge: Optional[float] = None
    helicity: Optional[float] = None
    divergence_residual: Optional[float] = None
    curl_residual: Optional[float] = None
    symmetries: list[str] = field(default_factory=list)
    conservation_residuals: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def max_residual(self) -> float:
        vals = list(self.conservation_residuals.values())
        if self.divergence_residual is not None:
            vals.append(abs(self.divergence_residual))
        if self.curl_residual is not None:
            vals.append(abs(self.curl_residual))
        return max(vals) if vals else 0.0


@dataclass
class Transition:
    transition_id: str
    initial_state: dict[str, Any]
    intervention: dict[str, Any]
    constraints: dict[str, Any]
    result_state: dict[str, Any]
    certificate: Certificate
    reversible: Optional[bool] = None
    stable: Optional[bool] = None
    created_at: float = field(default_factory=time.time)

    def preserves_invariants(self, tol: float = 1e-6) -> bool:
        return self.certificate.max_residual() <= tol


def make_transition(
    initial_state: dict[str, Any],
    intervention: dict[str, Any],
    result_state: dict[str, Any],
    certificate: Certificate,
    constraints: Optional[dict[str, Any]] = None,
) -> Transition:
    return Transition(
        transition_id=f"T_{uuid.uuid4().hex[:10]}",
        initial_state=initial_state,
        intervention=intervention,
        constraints=constraints or {},
        result_state=result_state,
        certificate=certificate,
        reversible=None,
        stable=certificate.max_residual() < 1e-3,
    )
