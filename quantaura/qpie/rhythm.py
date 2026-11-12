"""Energy-accounted rhythmic dynamics for coupled QPIE systems.

This module formalizes periodic forcing, coupled oscillators, damping, and
energy exchange. It is a classical numerical model, not a claim that all
nature follows a single universal pulse law.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


Drive = Callable[[float], np.ndarray]


@dataclass(frozen=True)
class RhythmSimulation:
    time: np.ndarray
    position: np.ndarray
    velocity: np.ndarray
    energy: np.ndarray
    cumulative_input_work: np.ndarray
    cumulative_dissipation: np.ndarray
    energy_balance_residual: np.ndarray

    @property
    def max_abs_energy_balance_residual(self) -> float:
        return float(np.max(np.abs(self.energy_balance_residual)))


def _matrix(value: np.ndarray, n: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        array = float(array) * np.eye(n)
    elif array.ndim == 1:
        if array.shape != (n,):
            raise ValueError(f"{name} vector must have shape ({n},)")
        array = np.diag(array)
    if array.shape != (n, n):
        raise ValueError(f"{name} must be scalar, length-{n} vector, or ({n}, {n}) matrix")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    if not np.allclose(array, array.T, atol=1e-10, rtol=0.0):
        raise ValueError(f"{name} must be symmetric")
    return array


def simulate_rhythmic_network(
    *,
    mass: np.ndarray,
    damping: np.ndarray,
    stiffness: np.ndarray,
    initial_position: np.ndarray,
    initial_velocity: np.ndarray,
    dt: float,
    steps: int,
    drive: Drive | None = None,
    actuation_matrix: np.ndarray | None = None,
    cubic_stiffness: np.ndarray | None = None,
) -> RhythmSimulation:
    """Integrate M x'' + C x' + K x + beta*x**3 = B u(t).

    If actuation_matrix B is omitted, drive(t) must return a generalized force
    with one value per degree of freedom. If B is supplied, drive(t) returns
    actuator inputs and B maps them into generalized forces.

    M must be positive definite; C and K must be positive semidefinite;
    beta must be nonnegative so the optional quartic potential is bounded.
    The fixed-step RK4 integrator is intended for controlled experiments.
    Convergence should be checked by reducing dt.
    """

    x0 = np.asarray(initial_position, dtype=float)
    v0 = np.asarray(initial_velocity, dtype=float)
    if x0.ndim != 1 or v0.shape != x0.shape or x0.size == 0:
        raise ValueError("initial position and velocity must be matching nonempty vectors")
    if not np.all(np.isfinite(x0)) or not np.all(np.isfinite(v0)):
        raise ValueError("initial conditions must be finite")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")
    if not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")

    n = x0.size
    m = _matrix(mass, n, "mass")
    c = _matrix(damping, n, "damping")
    k = _matrix(stiffness, n, "stiffness")

    try:
        np.linalg.cholesky(m)
    except np.linalg.LinAlgError as exc:
        raise ValueError("mass matrix must be positive definite") from exc

    tolerance = 1e-10
    if float(np.min(np.linalg.eigvalsh(c))) < -tolerance:
        raise ValueError("damping matrix must be positive semidefinite")
    if float(np.min(np.linalg.eigvalsh(k))) < -tolerance:
        raise ValueError("stiffness matrix must be positive semidefinite")

    if cubic_stiffness is None:
        beta = np.zeros(n, dtype=float)
    else:
        beta = np.asarray(cubic_stiffness, dtype=float)
        if beta.shape != (n,) or not np.all(np.isfinite(beta)) or np.any(beta < 0):
            raise ValueError("cubic_stiffness must be a finite nonnegative vector of length n")

    if actuation_matrix is not None:
        b = np.asarray(actuation_matrix, dtype=float)
        if b.ndim != 2 or b.shape[0] != n or not np.all(np.isfinite(b)):
            raise ValueError("actuation_matrix must be a finite (n, n_inputs) matrix")
        n_inputs = b.shape[1]
    else:
        b = None
        n_inputs = n

    def generalized_force(t: float) -> np.ndarray:
        if drive is None:
            return np.zeros(n, dtype=float)
        supplied = np.asarray(drive(t), dtype=float)
        expected = n_inputs if b is not None else n
        if supplied.shape != (expected,) or not np.all(np.isfinite(supplied)):
            raise ValueError(f"drive(t) must return a finite vector of length {expected}")
        return b @ supplied if b is not None else supplied

    def acceleration(t: float, x: np.ndarray, v: np.ndarray) -> np.ndarray:
        force = generalized_force(t)
        restoring = k @ x + beta * x**3
        return np.linalg.solve(m, force - c @ v - restoring)

    def rhs(t: float, state: np.ndarray) -> np.ndarray:
        x = state[:n]
        v = state[n:]
        return np.concatenate((v, acceleration(t, x, v)))

    times = np.arange(steps + 1, dtype=float) * dt
    states = np.zeros((steps + 1, 2 * n), dtype=float)
    states[0, :n] = x0
    states[0, n:] = v0

    for index in range(steps):
        t = times[index]
        y = states[index]
        k1 = rhs(t, y)
        k2 = rhs(t + dt / 2.0, y + dt * k1 / 2.0)
        k3 = rhs(t + dt / 2.0, y + dt * k2 / 2.0)
        k4 = rhs(t + dt, y + dt * k3)
        states[index + 1] = y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    positions = states[:, :n]
    velocities = states[:, n:]
    energies = (
        0.5 * np.einsum("ti,ij,tj->t", velocities, m, velocities)
        + 0.5 * np.einsum("ti,ij,tj->t", positions, k, positions)
        + 0.25 * np.sum(beta[None, :] * positions**4, axis=1)
    )

    input_power = np.empty(steps + 1, dtype=float)
    dissipated_power = np.empty(steps + 1, dtype=float)
    for index, t in enumerate(times):
        force = generalized_force(float(t))
        velocity = velocities[index]
        input_power[index] = float(velocity @ force)
        dissipated_power[index] = float(velocity @ c @ velocity)

    cumulative_work = np.zeros(steps + 1, dtype=float)
    cumulative_dissipation = np.zeros(steps + 1, dtype=float)
    cumulative_work[1:] = np.cumsum(
        0.5 * dt * (input_power[:-1] + input_power[1:])
    )
    cumulative_dissipation[1:] = np.cumsum(
        0.5 * dt * (dissipated_power[:-1] + dissipated_power[1:])
    )
    balance = energies - energies[0] - cumulative_work + cumulative_dissipation

    return RhythmSimulation(
        time=times,
        position=positions,
        velocity=velocities,
        energy=energies,
        cumulative_input_work=cumulative_work,
        cumulative_dissipation=cumulative_dissipation,
        energy_balance_residual=balance,
    )
