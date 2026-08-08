"""Schwinger / lattice-gauge quantum laboratory (small systems)."""

from .hamiltonian import build_schwinger_like_matrix, exact_spectrum, spectral_report

__all__ = ["build_schwinger_like_matrix", "exact_spectrum", "spectral_report"]
