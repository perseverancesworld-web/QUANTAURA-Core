"""VQE adapter interface — classical stub cross-checks ED for small n."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from quantaura.qpie.schwinger.hamiltonian import build_schwinger_like_matrix, exact_spectrum


@dataclass
class VQEResult:
    energy: float
    n_iterations: int
    backend: str
    reference_ed_ground: Optional[float]
    abs_error_vs_ed: Optional[float]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "energy": self.energy,
            "n_iterations": self.n_iterations,
            "backend": self.backend,
            "reference_ed_ground": self.reference_ed_ground,
            "abs_error_vs_ed": self.abs_error_vs_ed,
            "notes": self.notes,
        }


def classical_variational_stub(
    n_sites: int = 3,
    m: float = 0.5,
    h: float = 0.1,
    n_samples: int = 20,
    seed: int = 0,
) -> VQEResult:
    H = build_schwinger_like_matrix(n_sites, m, h)
    ed = exact_spectrum(n_sites, m, h)
    dim = H.shape[0]
    rng = np.random.default_rng(seed)
    best = float("inf")
    for _ in range(n_samples):
        v = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
        v = v / np.linalg.norm(v)
        e = float(np.real(np.vdot(v, H @ v)))
        best = min(best, e)
    return VQEResult(
        energy=best,
        n_iterations=n_samples,
        backend="classical_variational_stub",
        reference_ed_ground=ed.ground_energy,
        abs_error_vs_ed=abs(best - ed.ground_energy),
        notes="Random-state upper bounds; replace with circuit VQE for production",
    )
