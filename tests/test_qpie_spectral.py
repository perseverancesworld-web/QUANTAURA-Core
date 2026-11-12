"""Tests for gauge-covariant spectral and octave-analysis tools."""

import numpy as np
import pytest

from quantaura.qpie.gauge import LatticeGaugeU1
from quantaura.qpie.spectral import (
    frequencies_to_octave_bins,
    gauge_covariant_hamiltonian,
    gauge_transform,
    hermitian_spectrum,
    octave_histogram,
    stiffness_mode_frequencies,
)


def test_gauge_hamiltonian_is_hermitian():
    gauge = LatticeGaugeU1.random(5, 6, scale=0.3, seed=11)
    h = gauge_covariant_hamiltonian(gauge)
    report = hermitian_spectrum(h)
    assert report.hermitian_residual < 1e-12
    assert h.shape == (30, 30)


def test_gauge_transform_preserves_spectrum():
    gauge = LatticeGaugeU1.random(5, 6, scale=0.2, seed=7)
    alpha = np.random.default_rng(8).uniform(-np.pi, np.pi, size=(5, 6))

    h0 = gauge_covariant_hamiltonian(gauge)
    h1 = gauge_covariant_hamiltonian(gauge_transform(gauge, alpha))

    e0 = hermitian_spectrum(h0).eigenvalues
    e1 = hermitian_spectrum(h1).eigenvalues
    assert np.allclose(e0, e1, atol=1e-10, rtol=1e-10)


def test_zero_flux_torus_matches_analytic_free_spectrum():
    nx, ny = 3, 4
    h = gauge_covariant_hamiltonian(LatticeGaugeU1.zeros(nx, ny))
    measured = hermitian_spectrum(h).eigenvalues

    expected = []
    for kx in range(nx):
        for ky in range(ny):
            expected.append(
                4.0
                - 2.0 * np.cos(2.0 * np.pi * kx / nx)
                - 2.0 * np.cos(2.0 * np.pi * ky / ny)
            )
    assert np.allclose(measured, np.sort(expected), atol=1e-10)


def test_octave_bins_and_histogram():
    frequencies = np.array([0.5, 1.0, 1.99, 2.0, 4.0])
    assert frequencies_to_octave_bins(frequencies).tolist() == [-1, 0, 0, 1, 2]
    assert octave_histogram(frequencies) == {-1: 1, 0: 2, 1: 1, 2: 1}


def test_octave_bins_reject_nonpositive_frequency():
    with pytest.raises(ValueError):
        frequencies_to_octave_bins(np.array([1.0, 0.0]))


def test_stiffness_mode_frequencies_omit_rigid_mode():
    stiffness = np.diag([0.0, 4.0, 16.0])
    expected = np.array([1.0 / np.pi, 2.0 / np.pi])
    assert np.allclose(stiffness_mode_frequencies(stiffness), expected)


def test_stiffness_rejects_negative_mode():
    with pytest.raises(ValueError):
        stiffness_mode_frequencies(np.diag([-0.1, 1.0]))

def test_uniform_flux_torus_plaquettes_and_quantization():
    from quantaura.qpie.spectral import (
        principal_plaquette_phase,
        uniform_flux_gauge,
    )

    for flux in (0.0, np.pi / 6.0, np.pi / 3.0, np.pi / 2.0):
        gauge = uniform_flux_gauge(12, 12, flux)
        measured = principal_plaquette_phase(gauge)
        assert np.allclose(measured, flux, atol=1e-10)

    with pytest.raises(ValueError):
        uniform_flux_gauge(12, 12, 0.123)

