"""QPIE-27 — QUANTAURA Physical Intelligence Engine.

A computational laboratory for discovering emergent physics in coupled systems.
PRISM-MATTER is the programmable-material subsystem.

Core invariant (engine-level): no Tier-5 physics claims without human process.
Authorization of *actions* remains with the Execution Authorization Kernel.
"""

from quantaura.qpie.state_space import PhysicalStateSpace, empty_lattice_state
from quantaura.qpie.geometry import CommonGeometry, FormDegree, regular_grid_2d
from quantaura.qpie.gauge import LatticeGaugeU1, schwinger_like_hamiltonian_coeffs
from quantaura.qpie.topology import hopf_proxy_3d, skyrmion_density_2d
from quantaura.qpie.spectral import (
    SpectrumReport,
    frequencies_to_octave_bins,
    gauge_covariant_hamiltonian,
    gauge_transform,
    hermitian_spectrum,
    octave_histogram,
    stiffness_mode_frequencies,
    principal_plaquette_phase,
    uniform_flux_gauge,
)
from quantaura.qpie.rhythm import RhythmSimulation, simulate_rhythmic_network
from quantaura.qpie.vortex import helicity_3d, vorticity_2d
from quantaura.qpie.causal import CausalPhysicsGraph, default_physics_graph
from quantaura.qpie.transition import Certificate, Transition, make_transition
from quantaura.qpie.discovery import ExperimentScore, score_experiment
from quantaura.qpie.firewall import DiscoveryTier, classify_candidate
from quantaura.qpie.observatory import Observatory, PhysicalStateAgent
from quantaura.qpie.prism import MaterialConfiguration, default_metamaterial_seed
from quantaura.qpie.benchmarks.known_solutions import run_all_benchmarks

__all__ = [
    "PhysicalStateSpace",
    "empty_lattice_state",
    "CommonGeometry",
    "FormDegree",
    "regular_grid_2d",
    "LatticeGaugeU1",
    "schwinger_like_hamiltonian_coeffs",
    "hopf_proxy_3d",
    "skyrmion_density_2d",
    "SpectrumReport",
    "gauge_covariant_hamiltonian",
    "gauge_transform",
    "hermitian_spectrum",
    "frequencies_to_octave_bins",
    "octave_histogram",
    "stiffness_mode_frequencies",
    "principal_plaquette_phase",
    "uniform_flux_gauge",
    "RhythmSimulation",
    "simulate_rhythmic_network",
    "helicity_3d",
    "vorticity_2d",
    "CausalPhysicsGraph",
    "default_physics_graph",
    "Certificate",
    "Transition",
    "make_transition",
    "ExperimentScore",
    "score_experiment",
    "DiscoveryTier",
    "classify_candidate",
    "Observatory",
    "PhysicalStateAgent",
    "MaterialConfiguration",
    "default_metamaterial_seed",
    "run_all_benchmarks",
]
