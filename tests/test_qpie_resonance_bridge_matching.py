from quantaura.qpie.resonance_bridge import (
    EdgeElectricalSpec,
    NetworkEdge,
    NetworkModel,
    NetworkNode,
    matched_model_comparison,
)


def test_match_report_detects_changed_branch_parameter():
    nodes = [NetworkNode("a", shunt_conductance_s=0.01),
             NetworkNode("b", shunt_conductance_s=0.01)]
    baseline = NetworkModel(nodes, [NetworkEdge("e", "a", "b", EdgeElectricalSpec(4.0))])
    changed = NetworkModel(nodes, [NetworkEdge("e", "a", "b", EdgeElectricalSpec(5.0))])
    report = matched_model_comparison(baseline, changed)
    assert report["matched_nodes"]
    assert report["matched_topology"]
    assert not report["matched_branch_parameters"]
    assert not report["matched_complete_model"]


def test_match_report_separates_link_phase_variation():
    nodes = [NetworkNode("a"), NetworkNode("b")]
    baseline = NetworkModel(nodes, [NetworkEdge("e", "a", "b", phase_rad=0.0)])
    phased = NetworkModel(nodes, [NetworkEdge("e", "a", "b", phase_rad=0.25)])
    report = matched_model_comparison(baseline, phased)
    assert report["matched_except_link_phases"]
    assert not report["matched_link_phases"]
