"""Scan the STH-1 torus flux set with QPIE spectral tools."""

import numpy as np

from quantaura.qpie.spectral import (
    gauge_covariant_hamiltonian,
    hermitian_spectrum,
    principal_plaquette_phase,
    uniform_flux_gauge,
)


def main() -> None:
    fluxes = (0.0, np.pi / 6.0, np.pi / 3.0, np.pi / 2.0)
    for flux in fluxes:
        gauge = uniform_flux_gauge(12, 12, flux)
        spectrum = hermitian_spectrum(gauge_covariant_hamiltonian(gauge))
        rounded = np.round(spectrum.eigenvalues, decimals=8)
        unique, counts = np.unique(rounded, return_counts=True)
        phase = principal_plaquette_phase(gauge)
        print({
            "flux_per_plaquette": float(flux),
            "mean_plaquette_holonomy_real": float(np.mean(np.cos(phase))),
            "hermitian_residual": spectrum.hermitian_residual,
            "lowest_eigenvalues": spectrum.eigenvalues[:8].round(8).tolist(),
            "distinct_rounded_modes": int(unique.size),
            "largest_rounded_degeneracy": int(np.max(counts)),
        })


if __name__ == "__main__":
    main()
