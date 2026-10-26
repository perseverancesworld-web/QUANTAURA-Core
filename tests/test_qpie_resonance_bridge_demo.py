import json

from examples.resonance_bridge_demo import build_demo_record


def test_end_to_end_demo_returns_hashable_candidate_record():
    record = build_demo_record()
    assert record["schema"] == "qpie.resonance-bridge.experiment.v0.2"
    assert record["status"] == "CANDIDATE"
    assert len(record["sha256"]) == 64
    json.dumps(record, allow_nan=False)
    assert record["results"]["gauge_invariance"]["passed"] is True


def test_end_to_end_demo_uses_matched_controller_budget():
    record = build_demo_record()
    controllers = record["results"]["matched_budget_controller_benchmark"]["controllers"]
    assert len(controllers) == 3
    for result in controllers.values():
        assert result["budget_respected"] is True
        assert abs(result["total_displacement_consumed"] - 0.5) < 1e-9
