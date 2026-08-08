"""Lattice gauge layer: link variables U_ij and plaquette holonomy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class LatticeGaugeU1:
    """U(1) lattice gauge field on a 2D periodic grid."""

    theta_x: np.ndarray
    theta_y: np.ndarray

    @classmethod
    def zeros(cls, nx: int, ny: int) -> "LatticeGaugeU1":
        return cls(theta_x=np.zeros((nx, ny)), theta_y=np.zeros((nx, ny)))

    @classmethod
    def random(cls, nx: int, ny: int, scale: float = 0.1, seed: int | None = 0) -> "LatticeGaugeU1":
        rng = np.random.default_rng(seed)
        return cls(
            theta_x=scale * rng.standard_normal((nx, ny)),
            theta_y=scale * rng.standard_normal((nx, ny)),
        )

    @property
    def shape(self) -> Tuple[int, int]:
        return self.theta_x.shape  # type: ignore[return-value]

    def plaquette_phase(self) -> np.ndarray:
        tx, ty = self.theta_x, self.theta_y
        return tx + np.roll(ty, -1, axis=0) - np.roll(tx, -1, axis=1) - ty

    def plaquette_holonomy(self) -> np.ndarray:
        return np.exp(1j * self.plaquette_phase())

    def wilson_action(self, beta: float = 1.0) -> float:
        u = self.plaquette_holonomy()
        return float(beta * np.sum(1.0 - np.real(u)))

    def mean_field_strength(self) -> float:
        return float(np.mean(np.abs(self.plaquette_phase())))


def schwinger_like_hamiltonian_coeffs(n_sites: int = 4) -> dict:
    coeffs = []
    for i in range(n_sites - 1):
        coeffs.append({"pauli": f"Z{i}Z{i+1}", "c": 1.0})
    for i in range(n_sites):
        coeffs.append({"pauli": f"X{i}", "c": 0.5})
    return {"n_sites": n_sites, "terms": coeffs, "model": "schwinger_like_toy"}
