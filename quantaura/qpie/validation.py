"""Independent-solver validation: Solver A <-> Solver B <-> analytical."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class CrossSolverReport:
    name: str
    value_a: float
    value_b: float
    analytical: Optional[float]
    abs_err_ab: float
    abs_err_a_analytical: Optional[float]
    agreed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "analytical": self.analytical,
            "abs_err_ab": self.abs_err_ab,
            "abs_err_a_analytical": self.abs_err_a_analytical,
            "agreed": self.agreed,
        }


def compare_solvers(
    name: str,
    solver_a: Callable[[], float],
    solver_b: Callable[[], float],
    analytical: Optional[Callable[[], float]] = None,
    tol: float = 1e-6,
) -> CrossSolverReport:
    va, vb = float(solver_a()), float(solver_b())
    ana = float(analytical()) if analytical else None
    err_ab = abs(va - vb)
    err_a = abs(va - ana) if ana is not None else None
    agreed = err_ab <= tol and (err_a is None or err_a <= tol)
    return CrossSolverReport(name, va, vb, ana, err_ab, err_a, agreed)
