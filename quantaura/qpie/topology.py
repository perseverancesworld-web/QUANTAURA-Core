"""Topological laboratory: discrete Hopf / skyrmion proxies."""

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
    cx = np.cross(dy, dz)
    cy = np.cross(dz, dx)
    cz = np.cross(dx, dy)
    dens = (
        np.sum(n * cx, axis=-1)
        + np.sum(n * cy, axis=-1)
        + np.sum(n * cz, axis=-1)
    )
    hopf = float(np.sum(dens) / (4.0 * np.pi**2))
    mean_norm = float(np.mean(np.linalg.norm(n_field, axis=-1)))
    energy = float(np.mean(np.sum(dx**2 + dy**2 + dz**2, axis=-1)))
    return TopologicalReport(
        hopf_proxy=hopf,
        mean_norm=mean_norm,
        energy_proxy=energy,
        notes="discrete hopf-style proxy; validate against known maps before claims",
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
