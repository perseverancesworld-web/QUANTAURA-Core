"""Hermitian graph-operator adapter for QPIE lattice-gauge experiments.

This is an explicit tight-binding-style mathematical model on a graph. It is
not a hardware quantum simulator and does not imply quantum advantage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

import numpy as np

from quantaura.qpie.resonance_bridge import NetworkModel


@dataclass
class GraphHamiltonian:
    node_ids: tuple[str, ...]
    matrix: np.ndarray
    metadata: dict = field(default_factory=dict)

    def validate(self, tolerance: float = 1e-12) -> None:
        h = np.asarray(self.matrix, dtype=np.complex128)
        if h.shape != (len(self.node_ids), len(self.node_ids)):
            raise ValueError("Hamiltonian shape must match node_ids.")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("Hamiltonian node IDs must be unique.")
        if not np.isfinite(h.real).all() or not np.isfinite(h.imag).all():
            raise ValueError("Hamiltonian entries must be finite.")
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and nonnegative.")
        residual = float(np.max(np.abs(h - h.conj().T))) if h.size else 0.0
        if residual > tolerance:
            raise ValueError(f"Hamiltonian is not Hermitian; residual={residual:g}.")


def build_graph_hamiltonian(
    model: NetworkModel,
    onsite_energy: Mapping[str, float] | None = None,
    hopping_weights: Mapping[str, float] | None = None,
) -> GraphHamiltonian:
    """Build H_ij=-t exp(+i phi_ij); the reverse link is its conjugate.

    phase_rad is interpreted as a link phase for this discrete Hamiltonian
    adapter. It is not inferred from circuit impedance. Onsite energies and
    hopping magnitudes must be real; hopping magnitudes must be nonnegative.
    """
    model.validate()
    if not model.nodes:
        raise ValueError("Cannot build a Hamiltonian for an empty graph.")
    node_ids = tuple(node.node_id for node in model.nodes)
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    onsite = dict(onsite_energy or {})
    hops = dict(hopping_weights or {})
    if set(onsite) - set(node_ids):
        raise ValueError("onsite_energy references unknown node IDs.")
    if set(hops) - {edge.edge_id for edge in model.edges}:
        raise ValueError("hopping_weights references unknown edge IDs.")
    h = np.zeros((len(node_ids), len(node_ids)), dtype=np.complex128)
    for node_id, energy in onsite.items():
        energy = float(energy)
        if not math.isfinite(energy):
            raise ValueError("Onsite energies must be finite real values.")
        h[index[node_id], index[node_id]] = energy
    for edge in model.edges:
        weight = float(hops.get(edge.edge_id, edge.coupling_weight))
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"Hopping weight for {edge.edge_id} must be finite and nonnegative.")
        phase = complex(math.cos(edge.phase_rad), math.sin(edge.phase_rad))
        i, j = index[edge.source], index[edge.target]
        link = -weight * phase
        h[i, j] += link
        h[j, i] += link.conjugate()
    result = GraphHamiltonian(node_ids, h, {
        "operator": "graph-tight-binding",
        "phase_convention": "H[source,target]=-t*exp(+i*phase); reverse link is conjugate",
        "quantum_advantage_claim": False,
        "source_network": model.name,
    })
    result.validate()
    return result


def gauge_transform_hamiltonian(operator: GraphHamiltonian,
                                node_phases: Mapping[str, float]) -> GraphHamiltonian:
    """Apply local basis transform H' = U H U† with U_ii=exp(i theta_i)."""
    operator.validate()
    unknown = set(node_phases) - set(operator.node_ids)
    if unknown:
        raise ValueError(f"Gauge transform references unknown nodes: {sorted(unknown)}")
    theta = np.asarray([float(node_phases.get(node_id, 0.0)) for node_id in operator.node_ids])
    if not np.isfinite(theta).all():
        raise ValueError("Node gauge phases must be finite.")
    u = np.diag(np.exp(1j * theta))
    transformed = GraphHamiltonian(
        operator.node_ids,
        u @ np.asarray(operator.matrix, dtype=np.complex128) @ u.conj().T,
        {**operator.metadata, "gauge_transformed": True},
    )
    transformed.validate()
    return transformed


def diagonalize_graph_hamiltonian(operator: GraphHamiltonian,
                                  hermiticity_tolerance: float = 1e-12) -> dict:
    """Exact dense diagonalization for small systems; eigenvalues must be real."""
    operator.validate(hermiticity_tolerance)
    eigenvalues, eigenvectors = np.linalg.eigh(np.asarray(operator.matrix, dtype=np.complex128))
    ground = eigenvectors[:, 0]
    probabilities = np.abs(ground) ** 2
    return {
        "node_ids": list(operator.node_ids),
        "eigenvalues": [float(value) for value in eigenvalues],
        "ground_energy": float(eigenvalues[0]),
        "ground_state": {
            node_id: [float(ground[i].real), float(ground[i].imag)]
            for i, node_id in enumerate(operator.node_ids)
        },
        "ground_state_probabilities": {
            node_id: float(probabilities[i]) for i, node_id in enumerate(operator.node_ids)
        },
        "eigenvector_residual": float(np.linalg.norm(
            operator.matrix @ ground - eigenvalues[0] * ground
        )),
        "matrix_hermiticity_residual": float(np.max(np.abs(
            operator.matrix - operator.matrix.conj().T
        ))),
        "limitations": [
            "dense exact diagonalization is intended for small graphs",
            "operator is a declared mathematical model, not a hardware simulation",
            "no quantum-advantage claim is made",
        ],
    }


def gauge_invariance_report(operator: GraphHamiltonian, node_phases: Mapping[str, float],
                            tolerance: float = 1e-10) -> dict:
    """Check Hermiticity and spectral invariance under a local basis transform."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative.")
    operator.validate()
    transformed = gauge_transform_hamiltonian(operator, node_phases)
    before = np.linalg.eigvalsh(operator.matrix)
    after = np.linalg.eigvalsh(transformed.matrix)
    residual = float(np.max(np.abs(before - after))) if before.size else 0.0
    return {
        "schema": "qpie.resonance-bridge.gauge-report.v0.1",
        "passed": residual <= tolerance,
        "spectral_max_abs_residual": residual,
        "tolerance": tolerance,
        "hermitian_before": True,
        "hermitian_after": True,
        "transform": "H' = U H U†",
        "limitations": ["validates numerical gauge covariance of this discrete operator only",
                        "does not establish physical coupling or quantum advantage"],
    }
