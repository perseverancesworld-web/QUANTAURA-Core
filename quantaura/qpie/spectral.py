"""Gauge-covariant spectral tools for periodic QPIE lattices.

This module supplies testable spectral analogues of rhythmic/harmonic ideas.
It does not encode a new physical law or infer physical frequencies from an
arbitrary Hamiltonian without a separately specified physical model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantaura.qpie.gauge import LatticeGaugeU1


@dataclass(frozen=True)
class SpectrumReport:
    """Hermitian eigensystem and numerical symmetry diagnostic."""

    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    hermitian_residual: float


def gauge_transform(gauge: LatticeGaugeU1, site_phase: np.ndarray) -> LatticeGaugeU1:
    """Return the U(1)-transformed links for a site-dependent phase.

    With psi'(r) = exp(i alpha(r)) psi(r), links transform as
    U_mu'(r) = exp(i alpha(r)) U_mu(r) exp(-i alpha(r + mu)).
    """

    alpha = np.asarray(site_phase, dtype=float)
    if alpha.shape != gauge.shape:
        raise ValueError("site_phase must match the gauge lattice shape")
    if not np.all(np.isfinite(alpha)):
        raise ValueError("site_phase must contain only finite values")

    theta_x = gauge.theta_x + alpha - np.roll(alpha, -1, axis=0)
    theta_y = gauge.theta_y + alpha - np.roll(alpha, -1, axis=1)
    # Store canonical representatives in (-pi, pi].
    theta_x = np.angle(np.exp(1j * theta_x))
    theta_y = np.angle(np.exp(1j * theta_y))
    return LatticeGaugeU1(theta_x=theta_x, theta_y=theta_y)


def gauge_covariant_hamiltonian(
    gauge: LatticeGaugeU1,
    *,
    hopping: float = 1.0,
    potential: np.ndarray | None = None,
) -> np.ndarray:
    """Build a Hermitian nearest-neighbor operator on a periodic 2D torus.

    The operator is the magnetic graph Laplacian plus a real on-site
    potential. Its spectrum is invariant under local U(1) gauge changes.
    Energies are model-dependent; they are not automatically laboratory Hz.
    """

    theta_x = np.asarray(gauge.theta_x, dtype=float)
    theta_y = np.asarray(gauge.theta_y, dtype=float)
    if theta_x.ndim != 2 or theta_y.shape != theta_x.shape:
        raise ValueError("gauge links must be matching 2D arrays")
    nx, ny = theta_x.shape
    if nx < 3 or ny < 3:
        raise ValueError("periodic torus dimensions must each be at least 3")
    if not np.isfinite(hopping) or hopping <= 0:
        raise ValueError("hopping must be finite and positive")
    if not np.all(np.isfinite(theta_x)) or not np.all(np.isfinite(theta_y)):
        raise ValueError("gauge links must contain only finite values")

    if potential is None:
        onsite = np.zeros((nx, ny), dtype=float)
    else:
        onsite = np.asarray(potential, dtype=float)
        if onsite.shape != (nx, ny):
            raise ValueError("potential must match the gauge lattice shape")
        if not np.all(np.isfinite(onsite)):
            raise ValueError("potential must contain only finite values")

    def flat(i: int, j: int) -> int:
        return i * ny + j

    n_sites = nx * ny
    hamiltonian = np.zeros((n_sites, n_sites), dtype=complex)
    for i in range(nx):
        for j in range(ny):
            site = flat(i, j)
            hamiltonian[site, site] += 4.0 * hopping + onsite[i, j]

            x_neighbor = flat((i + 1) % nx, j)
            ux = np.exp(1j * theta_x[i, j])
            hamiltonian[site, x_neighbor] += -hopping * ux
            hamiltonian[x_neighbor, site] += -hopping * np.conjugate(ux)

            y_neighbor = flat(i, (j + 1) % ny)
            uy = np.exp(1j * theta_y[i, j])
            hamiltonian[site, y_neighbor] += -hopping * uy
            hamiltonian[y_neighbor, site] += -hopping * np.conjugate(uy)

    return hamiltonian


def hermitian_spectrum(
    operator: np.ndarray,
    *,
    tolerance: float = 1e-10,
) -> SpectrumReport:
    """Diagonalize a Hermitian operator after checking its residual."""

    matrix = np.asarray(operator, dtype=complex)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("operator must be a square matrix")
    if tolerance <= 0 or not np.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    residual = float(np.max(np.abs(matrix - matrix.conjugate().T)))
    if residual > tolerance:
        raise ValueError(
            f"operator is not Hermitian: residual {residual:.3e} exceeds tolerance"
        )
    values, vectors = np.linalg.eigh(matrix)
    return SpectrumReport(values, vectors, residual)


def frequencies_to_octave_bins(
    frequencies: np.ndarray,
    *,
    reference_frequency: float = 1.0,
) -> np.ndarray:
    """Assign positive frequencies to log2 bands relative to a reference.

    Band k contains [reference*2**k, reference*2**(k+1)). This is a neutral
    analysis convention, not evidence that physical systems obey Russell's
    proposed octave cosmology.
    """

    values = np.asarray(frequencies, dtype=float)
    if not np.isfinite(reference_frequency) or reference_frequency <= 0:
        raise ValueError("reference_frequency must be finite and positive")
    if values.size == 0:
        return np.asarray([], dtype=int)
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("frequencies must be finite and strictly positive")
    return np.floor(np.log2(values / reference_frequency)).astype(int)


def octave_histogram(
    frequencies: np.ndarray,
    *,
    reference_frequency: float = 1.0,
) -> dict[int, int]:
    """Count spectral modes in octave-width logarithmic bands."""

    bins = frequencies_to_octave_bins(
        frequencies, reference_frequency=reference_frequency
    )
    unique, counts = np.unique(bins, return_counts=True)
    return {int(band): int(count) for band, count in zip(unique, counts)}


def stiffness_mode_frequencies(
    stiffness: np.ndarray,
    *,
    mass: float = 1.0,
    tolerance: float = 1e-10,
) -> np.ndarray:
    """Return positive natural frequencies (Hz) for M=mI and K stiffness.

    Zero modes are omitted. This conversion is appropriate only when the
    supplied matrix is a physical stiffness matrix and mass is in consistent
    physical units; otherwise the result is a model-scale frequency.
    """

    matrix = np.asarray(stiffness, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("stiffness must be a square matrix")
    if not np.isfinite(mass) or mass <= 0:
        raise ValueError("mass must be finite and positive")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("stiffness must contain only finite values")
    if not np.allclose(matrix, matrix.T, atol=tolerance, rtol=0.0):
        raise ValueError("stiffness must be symmetric")

    eigenvalues = np.linalg.eigvalsh(matrix)
    if float(np.min(eigenvalues)) < -tolerance:
        raise ValueError("stiffness must be positive semidefinite")
    positive = eigenvalues[eigenvalues > tolerance]
    return np.sqrt(positive / mass) / (2.0 * np.pi)
