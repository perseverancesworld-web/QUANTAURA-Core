"""Topological laboratory: discrete proxies + analytical test fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import numpy as np


def normalize_field(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, eps)


@dataclass
class TopologicalReport:
    hopf_proxy: float
    mean_norm: float
    energy_proxy: float
    notes: str = ""


def hopf_proxy_3d(n_field: np.ndarray) -> TopologicalReport:
    if n_field.ndim != 4 or n_field.shape[-1] != 3:
        raise ValueError("n_field must have shape (nx, ny, nz, 3)")
    n = normalize_field(n_field)
    dx = np.roll(n, -1, axis=0) - n
    dy = np.roll(n, -1, axis=1) - n
    dz = np.roll(n, -1, axis=2) - n
    dens = (
        np.sum(n * np.cross(dy, dz), axis=-1)
        + np.sum(n * np.cross(dz, dx), axis=-1)
        + np.sum(n * np.cross(dx, dy), axis=-1)
    )
    hopf = float(np.sum(dens) / (4.0 * np.pi**2))
    return TopologicalReport(
        hopf_proxy=hopf,
        mean_norm=float(np.mean(np.linalg.norm(n_field, axis=-1))),
        energy_proxy=float(np.mean(np.sum(dx**2 + dy**2 + dz**2, axis=-1))),
        notes="discrete hopf-style proxy",
    )


def skyrmion_density_2d(n_field: np.ndarray) -> Tuple[np.ndarray, float]:
    if n_field.ndim != 3 or n_field.shape[-1] != 3:
        raise ValueError("n_field must have shape (nx, ny, 3)")
    n = normalize_field(n_field)
    dx = np.roll(n, -1, axis=0) - n
    dy = np.roll(n, -1, axis=1) - n
    dens = np.sum(n * np.cross(dx, dy), axis=-1)
    q = float(np.sum(dens) / (4.0 * np.pi))
    return dens, q


def uniform_field_3d(n: int = 8, axis: int = 2) -> np.ndarray:
    field = np.zeros((n, n, n, 3))
    field[..., axis] = 1.0
    return field


def baby_skyrmion_2d(n: int = 32, radius: float = 6.0) -> np.ndarray:
    xs = np.linspace(-n / 2, n / 2, n)
    ys = np.linspace(-n / 2, n / 2, n)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    r2 = X**2 + Y**2
    r0 = radius
    nz = (r0**2 - r2) / (r0**2 + r2 + 1e-12)
    nx = 2 * r0 * X / (r0**2 + r2 + 1e-12)
    ny = 2 * r0 * Y / (r0**2 + r2 + 1e-12)
    return normalize_field(np.stack([nx, ny, nz], axis=-1))


def topology_validation_suite() -> list[dict]:
    out = []
    _, q = skyrmion_density_2d(np.zeros((16, 16, 3)) + np.array([0, 0, 1.0]))
    out.append({"name": "uniform_skyrmion_Q", "Q": q, "passed": abs(q) < 0.05})
    field = baby_skyrmion_2d(48, radius=8.0)
    _, q2 = skyrmion_density_2d(field)
    out.append({"name": "baby_skyrmion_Q", "Q": q2, "passed": abs(abs(q2) - 1.0) < 0.25})
    rep = hopf_proxy_3d(uniform_field_3d(6))
    out.append({"name": "uniform_hopf_proxy", "hopf_proxy": rep.hopf_proxy, "passed": abs(rep.hopf_proxy) < 0.05})
    return out
