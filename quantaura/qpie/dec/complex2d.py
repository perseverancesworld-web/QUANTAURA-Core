"""2D periodic primal complex — DEC v0.5 with Hodge + conservation."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class GridComplex2D:
    nx: int
    ny: int
    spacing: float = 1.0

    @property
    def n0(self) -> int:
        return self.nx * self.ny

    @property
    def n1(self) -> int:
        return 2 * self.nx * self.ny

    @property
    def n2(self) -> int:
        return self.nx * self.ny

    def _node(self, i: int, j: int) -> int:
        return (i % self.nx) * self.ny + (j % self.ny)

    def _hx(self, i: int, j: int) -> int:
        return (i % self.nx) * self.ny + (j % self.ny)

    def _vy(self, i: int, j: int) -> int:
        return self.nx * self.ny + (i % self.nx) * self.ny + (j % self.ny)

    def _face(self, i: int, j: int) -> int:
        return (i % self.nx) * self.ny + (j % self.ny)

    def incidence_d0(self) -> np.ndarray:
        d0 = np.zeros((self.n1, self.n0), dtype=float)
        for i in range(self.nx):
            for j in range(self.ny):
                e = self._hx(i, j)
                d0[e, self._node(i + 1, j)] += 1.0
                d0[e, self._node(i, j)] -= 1.0
                e = self._vy(i, j)
                d0[e, self._node(i, j + 1)] += 1.0
                d0[e, self._node(i, j)] -= 1.0
        return d0

    def incidence_d1(self) -> np.ndarray:
        d1 = np.zeros((self.n2, self.n1), dtype=float)
        for i in range(self.nx):
            for j in range(self.ny):
                f = self._face(i, j)
                d1[f, self._hx(i, j)] += 1.0
                d1[f, self._vy(i + 1, j)] += 1.0
                d1[f, self._hx(i, j + 1)] -= 1.0
                d1[f, self._vy(i, j)] -= 1.0
        return d1

    def hodge_star_0(self) -> np.ndarray:
        return np.eye(self.n0) * (self.spacing**2)

    def hodge_star_1(self) -> np.ndarray:
        return np.eye(self.n1) * 1.0

    def hodge_star_2(self) -> np.ndarray:
        return np.eye(self.n2) / (self.spacing**2)

    def codifferential_1(self) -> np.ndarray:
        d0 = self.incidence_d0()
        return -np.linalg.inv(self.hodge_star_0()) @ d0.T @ self.hodge_star_1()

    def laplacian_0(self) -> np.ndarray:
        return self.codifferential_1() @ self.incidence_d0()


def exterior_derivative(complex2d: GridComplex2D, form_degree: int, values: np.ndarray) -> np.ndarray:
    if form_degree == 0:
        return complex2d.incidence_d0() @ values.reshape(-1)
    if form_degree == 1:
        return complex2d.incidence_d1() @ values.reshape(-1)
    raise ValueError("Only d0 and d1 supported")


def discrete_gradient(complex2d: GridComplex2D, scalar: np.ndarray) -> np.ndarray:
    return exterior_derivative(complex2d, 0, scalar)


def discrete_curl(complex2d: GridComplex2D, edge_form: np.ndarray) -> np.ndarray:
    return exterior_derivative(complex2d, 1, edge_form)


def discrete_div(complex2d: GridComplex2D, edge_form: np.ndarray) -> np.ndarray:
    return complex2d.codifferential_1() @ edge_form.reshape(-1)


def conservation_report(complex2d: GridComplex2D, rng: np.random.Generator | None = None) -> dict:
    rng = rng or np.random.default_rng(0)
    d0, d1 = complex2d.incidence_d0(), complex2d.incidence_d1()
    d2_res = float(np.max(np.abs(d1 @ d0)))
    f = rng.standard_normal(complex2d.n0)
    curl_grad = float(np.max(np.abs(discrete_curl(complex2d, discrete_gradient(complex2d, f)))))
    L = complex2d.laplacian_0()
    sym = float(np.max(np.abs(L - L.T)))
    return {
        "d2_residual": d2_res,
        "curl_grad_residual": curl_grad,
        "laplacian_asymmetry": sym,
        "passed": d2_res < 1e-12 and curl_grad < 1e-10 and sym < 1e-10,
    }
