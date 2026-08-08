"""Known-solution benchmarks."""

from .known_solutions import (
    test_plaquette_identity_flat,
    test_helicity_zero_potential_flow,
    test_firewall_blocks_tier5,
    run_all_benchmarks,
)

__all__ = [
    "test_plaquette_identity_flat",
    "test_helicity_zero_potential_flow",
    "test_firewall_blocks_tier5",
    "run_all_benchmarks",
]
