import pytest

from quantaura.qpie.resonance_bridge import MechanicalBond, MechanicalGraph
from quantaura.qpie.resonance_bridge_control import run_controller_benchmark


def square_graph():
    return MechanicalGraph(
        positions={"a": (0.0, 0.0), "b": (1.0, 0.0),
                   "c": (1.0, 1.0), "d": (0.0, 1.0)},
        bonds=[MechanicalBond("ab", "a", "b", stiffness=1.0),
               MechanicalBond("bc", "b", "c", stiffness=2.0),
               MechanicalBond("cd", "c", "d", stiffness=1.0)],
    )


def targets():
    return {"a": (0.2, 0.1), "b": (1.2, -0.1),
            "c": (0.8, 1.3), "d": (-0.2, 0.9)}


def test_all_controllers_share_fixed_node_set_and_budget():
    graph = square_graph()
    result = run_controller_benchmark(
        graph, targets(), total_displacement_budget=2.0,
        geometric_edges=[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")],
    )
    assert result["fixed_topology_during_controller_step"] is True
    assert set(result["controllers"]) == {
        "global_gradient", "local_geometric_neighbor", "topology_aware_local"
    }
    for row in result["controllers"].values():
        assert row["budget_respected"] is True
        assert row["total_displacement_consumed"] == pytest.approx(2.0)
        assert row["displacement_budget"] == 2.0


def test_mechanical_bond_failure_changes_topology_aware_baseline():
    graph = square_graph()
    geo_edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")]
    intact = run_controller_benchmark(graph, targets(), 1.0, geometric_edges=geo_edges)
    faulted = run_controller_benchmark(graph.without_bonds(["bc"]), targets(), 1.0,
                                       geometric_edges=geo_edges)
    assert intact["mechanical_bond_count"] == 3
    assert faulted["mechanical_bond_count"] == 2
    assert intact["controllers"]["topology_aware_local"]["commands"] != \
           faulted["controllers"]["topology_aware_local"]["commands"]


def test_zero_budget_produces_zero_actuation():
    result = run_controller_benchmark(square_graph(), targets(), 0.0,
        geometric_edges=[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])
    assert all(row["total_displacement_consumed"] == 0.0
               for row in result["controllers"].values())
