"""Toy staggered-inspired spin Hamiltonian + exact diagonalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np


def _pauli():
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return I, X, Y, Z


def _embed(op: np.ndarray, site: int, n: int) -> np.ndarray:
    I, _, _, _ = _pauli()
    mats = [op if i == site else I for i in range(n)]
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def build_schwinger_like_matrix(n_sites: int = 4, m: float = 0.5, h: float = 0.1) -> np.ndarray:
    if n_sites < 2 or n_sites > 10:
        raise ValueError("n_sites must be in [2, 10] for dense ED")
    _, X, Y, Z = _pauli()
    dim = 2**n_sites
    H = np.zeros((dim, dim), dtype=complex)
    for i in range(n_sites - 1):
        H += _embed(X, i, n_sites) @ _embed(X, i + 1, n_sites)
        H += _embed(Y, i, n_sites) @ _embed(Y, i + 1, n_sites)
    for i in range(n_sites):
        stagger = 1.0 if i % 2 == 0 else -1.0
        H += m * stagger * _embed(Z, i, n_sites)
        H += h * _embed(X, i, n_sites)
    return 0.5 * (H + H.conj().T)


@dataclass
class SpectrumReport:
    n_sites: int
    eigenvalues: list[float]
    gap: float
    ground_energy: float
    backend: str
    parameters: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_sites": self.n_sites,
            "eigenvalues": self.eigenvalues,
            "gap": self.gap,
            "ground_energy": self.ground_energy,
            "backend": self.backend,
            "parameters": self.parameters,
        }


def exact_spectrum(n_sites: int = 4, m: float = 0.5, h: float = 0.1) -> SpectrumReport:
    H = build_schwinger_like_matrix(n_sites, m, h)
    evals = np.sort(np.real(np.linalg.eigvalsh(H)))
    gap = float(evals[1] - evals[0]) if len(evals) > 1 else 0.0
    return SpectrumReport(
        n_sites=n_sites,
        eigenvalues=[float(x) for x in evals.tolist()],
        gap=gap,
        ground_energy=float(evals[0]),
        backend="exact_diagonalization",
        parameters={"m": m, "h": h},
    )


def spectral_report(n_sites: int = 4, m: float = 0.5, h: float = 0.1) -> dict[str, Any]:
    return exact_spectrum(n_sites, m, h).to_dict()
