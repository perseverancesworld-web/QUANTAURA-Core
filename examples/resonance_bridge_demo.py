"""End-to-end, no-side-effect demo of the QPIE Resonance Bridge."""

from __future__ import annotations

import json

from quantaura.qpie import (
    EdgeElectricalSpec,
    EvidenceStatus,
    MechanicalBond,
    MechanicalGraph,
    NetworkEdge,
    NetworkModel,
    build_graph_hamiltonian,
    diagonalize_graph_hamiltonian,
    fault_sensitivity_report,
    gauge_invariance_report,
    make_experiment_record,
    mechanical_to_network,
    run_controller_benchmark,
    smith_metrics,
    solve_ac_network,
)


def build_demo_record() -> dict:
    """Run a deterministic synthetic benchmark; no hardware or actuation is used."""
    graph = MechanicalGraph(
        positions={
            "a": (0.0, 0.0),
            "b": (1.0, 0.0),
            "c": (1.0, 1.0),
            "d": (0.0, 1.0),
        },
        bonds=[
            MechanicalBond("ab", "a", "b", stiffness=1.0, material="synthetic-A"),
            MechanicalBond("bc", "b", "c", stiffness=2.0, material="synthetic-A"),
            MechanicalBond("cd", "c", "d", stiffness=1.0, material="synthetic-B"),
            MechanicalBond("da", "d", "a", stiffness=0.8, material="synthetic-B"),
        ],
        metadata={"geometry": "unit-square", "status": "synthetic"},
    )
    electrical = {
        "ab": EdgeElectricalSpec(4.0, 1.0e-3, 1.0e-9),
        "bc": EdgeElectricalSpec(5.0, 1.5e-3, 1.2e-9),
        "cd": EdgeElectricalSpec(4.5, 0.8e-3, 0.8e-9),
        "da": EdgeElectricalSpec(6.0, 1.2e-3, 1.1e-9),
    }
    network = mechanical_to_network(graph, electrical, default_shunt_conductance_s=1.0e-3)
    frequency_hz = 1000.0
    voltages = solve_ac_network(network, frequency_hz, {"a": 1.0e-3 + 0j})
    fault_report = fault_sensitivity_report(network, frequency_hz, {"a": 1.0e-3 + 0j}, "c")

    geometric_edges = [
        ("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")
    ]
    controller_report = run_controller_benchmark(
        graph,
        {"a": (0.15, 0.08), "b": (1.10, -0.10),
         "c": (0.85, 1.20), "d": (-0.10, 0.95)},
        total_displacement_budget=0.5,
        geometric_edges=geometric_edges,
    )

    # A separate discrete Hamiltonian interpretation of edge link phases.
    link_phases = {"ab": 0.20, "bc": -0.40, "cd": 0.15, "da": 0.05}
    operator_network = NetworkModel(
        nodes=list(network.nodes),
        edges=[
            NetworkEdge(
                edge_id=edge.edge_id,
                source=edge.source,
                target=edge.target,
                electrical=edge.electrical,
                coupling_weight=edge.coupling_weight,
                phase_rad=link_phases[edge.mechanical_bond_id],
                mechanical_bond_id=edge.mechanical_bond_id,
            )
            for edge in network.edges
        ],
        name="resonance-bridge-phased-graph",
        metadata={"phase_model": "discrete-link-phase; separate from AC branch impedance"},
    )
    operator = build_graph_hamiltonian(operator_network)
    spectrum = diagonalize_graph_hamiltonian(operator)
    gauge_report = gauge_invariance_report(
        operator, {"a": 0.33, "b": -1.2, "c": 2.0, "d": -0.65}
    )

    first_branch_z = 1 / network.edges[0].electrical.admittance(frequency_hz)
    smith = smith_metrics(first_branch_z / 50.0)
    results = {
        "ac_node_voltages_v": voltages,
        "smith_metrics_first_branch_50_ohm_reference": smith,
        "fault_sensitivity": fault_report,
        "matched_budget_controller_benchmark": controller_report,
        "graph_hamiltonian_spectrum": spectrum,
        "gauge_invariance": gauge_report,
    }
    return make_experiment_record(
        model=network,
        parameters={
            "frequency_hz": frequency_hz,
            "source_current_a": {"a": [1.0e-3, 0.0]},
            "smith_reference_impedance_ohm": 50.0,
            "controller_total_displacement_budget": 0.5,
            "link_phase_radians": link_phases,
        },
        results=results,
        metadata={
            "experiment_id": "RB-M001",
            "purpose": "integrated smoke test across impedance, graph, topology, control, and gauge adapter",
            "all_inputs_synthetic": True,
        },
        status=EvidenceStatus.CANDIDATE,
    )


def main() -> None:
    print(json.dumps(build_demo_record(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
