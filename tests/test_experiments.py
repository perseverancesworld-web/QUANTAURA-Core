from quantaura.core.experiments import ExperimentConfig, run_experiment


def test_nested_experiment():
    cfg = ExperimentConfig.from_dict(
        {
            "name": "root",
            "model": "growth",
            "n_steps": 3,
            "initial_state": {"population": 10.0, "growth_rate": 0.1},
            "nested": [{"name": "child", "model": "growth", "n_steps": 2}],
        }
    )
    result = run_experiment(cfg)
    assert result.final_state["population"] > 10.0
    assert len(result.nested_results) == 1
