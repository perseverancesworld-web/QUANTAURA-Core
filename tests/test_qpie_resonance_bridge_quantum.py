import numpy as np
import pytest

from quantaura.qpie.resonance_bridge import NetworkEdge, NetworkModel, NetworkNode
from quantaura.qpie.resonance_bridge_quantum import (
    GraphHamiltonian,
    build_graph_hamiltonian,
    diagonalize_graph_hamiltonian,
    gauge_invariance_report,
    gauge_transform_hamiltonian,
)


def phased_triangle():
    return NetworkModel(
        name="phased-triangle",
        nodes=[NetworkNode("a"), NetworkNode("b"), NetworkNode("c")],
        edges=[
            NetworkEdge("ab", "a", "b", coupling_weight=1.0, phase_rad=0.2),
            NetworkEdge("bc", "b", "c", coupling_weight=0.7, phase_rad=-0.4),
            NetworkEdge("ca", "c", "a", coupling_weight=0.9, phase_rad=0.1),
        ],
    )


def test_graph_hamiltonian_is_hermitian():
    op = build_graph_hamiltonian(phased_triangle(), onsite_energy={"a": 0.1, "b": 0.2})
    op.validate()
    assert np.max(np.abs(op.matrix - op.matrix.conj().T)) < 1e-12
    assert op.metadata["quantum_advantage_claim"] is False


def test_exact_diagonalization_returns_normalized_ground_state():
    op = build_graph_hamiltonian(phased_triangle())
    result = diagonalize_graph_hamiltonian(op)
    assert len(result["eigenvalues"]) == 3
    assert result["eigenvalues"] == sorted(result["eigenvalues"])
    assert sum(result["ground_state_probabilities"].values()) == pytest.approx(1.0)
    assert result["eigenvector_residual"] < 1e-10


def test_gauge_transform_preserves_spectrum():
    op = build_graph_hamiltonian(phased_triangle())
    phases = {"a": 0.33, "b": -1.2, "c": 2.0}
    report = gauge_invariance_report(op, phases, tolerance=1e-10)
    transformed = gauge_transform_hamiltonian(op, phases)
    assert report["passed"]
    assert report["spectral_max_abs_residual"] < 1e-10
    assert not np.allclose(op.matrix, transformed.matrix)


def test_invalid_operator_is_rejected():
    bad = GraphHamiltonian(("a", "b"), np.array([[0, 1], [0, 0]], dtype=complex))
    with pytest.raises(ValueError, match="not Hermitian"):
        bad.validate()


def test_hamiltonian_rejects_unknown_hopping_edge():
    with pytest.raises(ValueError, match="unknown edge"):
        build_graph_hamiltonian(phased_triangle(), hopping_weights={"missing": 1.0})
