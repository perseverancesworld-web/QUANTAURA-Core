import math
import numpy as np
import pytest

from quantaura.qpie.resonance_bridge import (
    EdgeElectricalSpec, EvidenceStatus, MechanicalBond, MechanicalGraph,
    NetworkEdge, NetworkModel, NetworkNode, SeriesRLC, delaunay_edges,
    evaluate_promotion_gate, fault_sensitivity_report, gamma_to_impedance,
    impedance_to_gamma, make_experiment_record, matched_model_comparison,
    mechanical_to_network, propagate_complex_state, smith_metrics,
    solve_ac_network, to_physical_state_space,
)


def small_grounded_model():
    return NetworkModel(
        name="two-node-test",
        nodes=[NetworkNode("a", shunt_conductance_s=1.0),
               NetworkNode("b", shunt_conductance_s=1.0)],
        edges=[NetworkEdge("e1", "a", "b", EdgeElectricalSpec(1.0))],
    )


def test_smith_chart_round_trip_and_match():
    z = 0.7 + 0.4j
    gamma = impedance_to_gamma(z)
    recovered = gamma_to_impedance(gamma)
    assert recovered.real == pytest.approx(z.real)
    assert recovered.imag == pytest.approx(z.imag)
    assert impedance_to_gamma(1 + 0j) == 0j
    assert smith_metrics(1 + 0j)["vswr"] == 1.0


def test_smith_singularities_raise():
    with pytest.raises(ValueError):
        impedance_to_gamma(-1 + 0j)
    with pytest.raises(ValueError):
        gamma_to_impedance(1 + 0j)


def test_series_rlc_reactance():
    z = SeriesRLC(5.0, inductance_h=1e-3).impedance(1000.0)
    assert z.real == pytest.approx(5.0)
    assert z.imag == pytest.approx(2 * math.pi * 1000 * 1e-3)


def test_ac_nodal_solver_is_finite():
    result = solve_ac_network(small_grounded_model(), 1000.0, {"a": 1.0 + 0j})
    assert set(result) == {"a", "b"}
    assert all(math.isfinite(v.real) and math.isfinite(v.imag) for v in result.values())
    assert abs(result["a"]) > abs(result["b"])


def test_ac_solver_fails_for_floating_singular_network():
    model = NetworkModel([NetworkNode("a"), NetworkNode("b")],
                         [NetworkEdge("e", "a", "b")])
    with pytest.raises(np.linalg.LinAlgError):
        solve_ac_network(model, 1000, {"a": 1.0})


def test_mechanical_fault_does_not_change_geometry():
    graph = MechanicalGraph(
        positions={"a": (0.0, 0.0), "b": (1.0, 0.0), "c": (1.0, 1.0)},
        bonds=[MechanicalBond("ab", "a", "b"), MechanicalBond("bc", "b", "c")],
    )
    faulted = graph.without_bonds(["ab"])
    assert faulted.positions == graph.positions
    assert [b.bond_id for b in faulted.bonds] == ["bc"]
    assert [b.bond_id for b in graph.bonds] == ["ab", "bc"]


def test_mechanical_adapter_requires_explicit_mapping():
    graph = MechanicalGraph({"a": (0, 0), "b": (1, 0)}, [MechanicalBond("bond-1", "a", "b")])
    with pytest.raises(ValueError, match="mapping mismatch"):
        mechanical_to_network(graph, {})
    model = mechanical_to_network(graph, {"bond-1": EdgeElectricalSpec(4.0)})
    assert model.edges[0].mechanical_bond_id == "bond-1"


def test_delaunay_edges_are_geometric_only():
    pytest.importorskip("scipy")
    points = {"a": (0, 0), "b": (1, 0), "c": (0, 1), "d": (1, 1)}
    edges = delaunay_edges(points)
    assert all(a in points and b in points for a, b in edges)
    assert ("a", "b") in edges


def test_matched_model_comparison_detects_topology_change():
    model = small_grounded_model()
    result = matched_model_comparison(model, model.without_edges(["e1"]))
    assert result["matched_nodes"]
    assert not result["matched_topology"]
    assert not result["matched_edge_count"]


def test_fault_sensitivity_reports_each_edge():
    report = fault_sensitivity_report(small_grounded_model(), 100.0, {"a": 1.0}, "b")
    assert report["schema"].endswith("fault-report.v0.1")
    assert report["rows"][0]["status"] in {"solved", "singular_after_fault"}


def test_complex_graph_propagation_shape_and_finiteness():
    model = NetworkModel([NetworkNode("a"), NetworkNode("b")],
                         [NetworkEdge("e", "a", "b", coupling_weight=0.1)])
    history = propagate_complex_state(model, {"a": 1 + 0j}, dt=0.01, steps=10)
    assert len(history) == 11
    assert all(math.isfinite(x.real) and math.isfinite(x.imag)
               for frame in history for x in frame.values())


def test_qpie_state_space_adapter():
    state = to_physical_state_space(small_grounded_model(), 50.0)
    assert state.geometry["kind"] == "network_graph"
    assert state.fields["edge_admittance_real"].shape == (1,)
    assert state.metadata["scientific_status"] == "CANDIDATE"


def test_promotion_gate_fails_closed():
    denied = evaluate_promotion_gate(requested_status="VALIDATED", tests_passed=True,
                                     matched_classical_baseline=True)
    assert not denied["accepted"]
    assert denied["effective_status"] == "CANDIDATE"
    accepted = evaluate_promotion_gate(
        requested_status=EvidenceStatus.VALIDATED, tests_passed=True,
        matched_classical_baseline=True, independent_reproduction=True, human_reviewed=True)
    assert accepted["accepted"]


def test_experiment_record_is_deterministic_and_hashed():
    args = dict(model=small_grounded_model(), parameters={"frequency_hz": 1000},
                results={"error": 0.01})
    first, second = make_experiment_record(**args), make_experiment_record(**args)
    assert first["sha256"] == second["sha256"]
    assert len(first["sha256"]) == 64
    assert first["schema"] == "qpie.resonance-bridge.experiment.v0.2"

def test_ac_nodal_solver_matches_hand_derived_two_node_solution():
    # At DC: each node has 1 S to ground, the connecting resistor is 1 ohm (1 S),
    # and 1 A enters node a. Y=[[2,-1],[-1,2]], so V=[2/3,1/3].
    voltages = solve_ac_network(small_grounded_model(), 0.0, {"a": 1.0 + 0j})
    assert voltages["a"].real == pytest.approx(2.0 / 3.0)
    assert voltages["b"].real == pytest.approx(1.0 / 3.0)
    assert voltages["a"].imag == pytest.approx(0.0, abs=1e-12)
    assert voltages["b"].imag == pytest.approx(0.0, abs=1e-12)

def test_mechanical_bond_fault_does_not_rewrite_delaunay_geometry():
    pytest.importorskip("scipy")
    graph = MechanicalGraph(
        positions={"a": (0, 0), "b": (1, 0), "c": (1, 1), "d": (0, 1)},
        bonds=[MechanicalBond("ab", "a", "b"), MechanicalBond("bc", "b", "c")],
    )
    geometric_neighbors = delaunay_edges(graph.positions)
    faulted = graph.without_bonds(["ab"])
    assert delaunay_edges(faulted.positions) == geometric_neighbors
    assert ("a", "b") in geometric_neighbors
    assert all(bond.bond_id != "ab" for bond in faulted.bonds)
