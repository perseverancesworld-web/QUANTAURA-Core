"""Vortex / fluid layer: vorticity and helicity."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class FluidReport:
    helicity: float
    enstrophy: float
    kinetic_energy: float
    mean_vorticity_norm: float


def vorticity_2d(u: np.ndarray, v: np.ndarray, dx: float = 1.0) -> np.ndarray:
    dvdx = (np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0)) / (2.0 * dx)
    dudy = (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1)) / (2.0 * dx)
    return dvdx - dudy


def helicity_3d(velocity: np.ndarray, dx: float = 1.0) -> FluidReport:
    if velocity.ndim != 4 or velocity.shape[-1] != 3:
        raise ValueError("velocity must be (nx,ny,nz,3)")
    vx, vy, vz = velocity[..., 0], velocity[..., 1], velocity[..., 2]

    def d_dx(f):
        return (np.roll(f, -1, axis=0) - np.roll(f, 1, axis=0)) / (2.0 * dx)

    def d_dy(f):
        return (np.roll(f, -1, axis=1) - np.roll(f, 1, axis=1)) / (2.0 * dx)

    def d_dz(f):
        return (np.roll(f, -1, axis=2) - np.roll(f, 1, axis=2)) / (2.0 * dx)

    wx = d_dy(vz) - d_dz(vy)
    wy = d_dz(vx) - d_dx(vz)
    wz = d_dx(vy) - d_dy(vx)
    omega = np.stack([wx, wy, wz], axis=-1)
    helicity = float(np.sum(velocity * omega) * (dx**3))
    enstrophy = float(0.5 * np.sum(omega**2) * (dx**3))
    ke = float(0.5 * np.sum(velocity**2) * (dx**3))
    mean_w = float(np.mean(np.linalg.norm(omega, axis=-1)))
    return FluidReport(
        helicity=helicity,
        enstrophy=enstrophy,
        kinetic_energy=ke,
        mean_vorticity_norm=mean_w,
    )
