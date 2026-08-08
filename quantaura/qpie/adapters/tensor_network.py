"""Tensor-network adapter interface for spectral estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from quantaura.qpie.schwinger.hamiltonian import (
    build_schwinger_like_matrix,
    exact_spectrum,
    sparse_spectrum,
)


@dataclass
class TNSpectrumResult:
    n_sites: int
    ground_energy: float
    gap: float | None
    backend: str
    bond_dim: int
    parameters: dict[str, float]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_sites": self.n_sites,
            "ground_energy": self.ground_energy,
            "gap": self.gap,
            "backend": self.backend,
            "bond_dim": self.bond_dim,
            "parameters": self.parameters,
            "notes": self.notes,
        }


class TensorNetworkBackend(Protocol):
    def spectrum(self, n_sites: int, m: float, h: float, bond_dim: int = 16) -> TNSpectrumResult: ...


class ExactTNProxy:
    """Reference TN that uses dense ED — proves the contract."""

    def spectrum(self, n_sites: int, m: float = 0.5, h: float = 0.1, bond_dim: int = 16) -> TNSpectrumResult:
        ed = exact_spectrum(n_sites, m, h)
        return TNSpectrumResult(
            n_sites=n_sites,
            ground_energy=ed.ground_energy,
            gap=ed.gap,
            backend="exact_tn_proxy",
            bond_dim=bond_dim,
            parameters={"m": m, "h": h},
            notes="Proxy using dense ED; replace with MPS/DMRG for large n",
        )


class TruncatedSubspaceProxy:
    """Random subspace Rayleigh–Ritz upper bound (not MPS)."""

    def spectrum(
        self,
        n_sites: int,
        m: float = 0.5,
        h: float = 0.1,
        bond_dim: int = 16,
        seed: int = 0,
    ) -> TNSpectrumResult:
        H = build_schwinger_like_matrix(n_sites, m, h)
        dim = H.shape[0]
        k = min(max(bond_dim, 2), dim)
        rng = np.random.default_rng(seed)
        Q, _ = np.linalg.qr(rng.standard_normal((dim, k)) + 1j * rng.standard_normal((dim, k)))
        Heff = Q.conj().T @ H @ Q
        evals = np.sort(np.real(np.linalg.eigvalsh(Heff)))
        gap = float(evals[1] - evals[0]) if len(evals) > 1 else None
        return TNSpectrumResult(
            n_sites=n_sites,
            ground_energy=float(evals[0]),
            gap=gap,
            backend="truncated_subspace_proxy",
            bond_dim=k,
            parameters={"m": m, "h": h},
            notes="Random subspace upper bound on E0",
        )


def cross_validate_ed_tn(
    n_sites: int = 4,
    m: float = 0.5,
    h: float = 0.1,
    bond_dim: int = 8,
    tol: float = 1e-6,
) -> dict[str, Any]:
    ed = exact_spectrum(n_sites, m, h)
    proxy = ExactTNProxy().spectrum(n_sites, m, h, bond_dim=bond_dim)
    trunc = TruncatedSubspaceProxy().spectrum(n_sites, m, h, bond_dim=bond_dim)
    err_proxy = abs(ed.ground_energy - proxy.ground_energy)
    variational_ok = trunc.ground_energy >= ed.ground_energy - 1e-8
    return {
        "name": "ed_vs_tn_cross_validate",
        "ed_ground": ed.ground_energy,
        "tn_proxy_ground": proxy.ground_energy,
        "truncated_ground": trunc.ground_energy,
        "err_proxy": err_proxy,
        "proxy_passed": err_proxy < tol,
        "variational_ok": variational_ok,
        "passed": err_proxy < tol and variational_ok,
        "backends": [ed.backend, proxy.backend, trunc.backend],
    }


def cross_validate_sparse_tn(n_sites: int = 5, m: float = 0.5, h: float = 0.1) -> dict[str, Any]:
    sparse = sparse_spectrum(n_sites, m, h, k=4)
    proxy = ExactTNProxy().spectrum(n_sites, m, h)
    err = abs(sparse.ground_energy - proxy.ground_energy)
    return {
        "name": "sparse_vs_tn_proxy",
        "sparse_ground": sparse.ground_energy,
        "tn_ground": proxy.ground_energy,
        "abs_err": err,
        "passed": err < 1e-6,
    }
