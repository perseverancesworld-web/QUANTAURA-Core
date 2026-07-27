"""Tests for simulation, math, cognitive, and quant modules."""

from quantaura.core.simulation import SimulationEngine, simple_growth_step, nested_market_step
from quantaura.core.math_models import shannon_entropy, normalize, kl_divergence
from quantaura.core.cognitive import build_default_architecture
from quantaura.core.quant import Portfolio, simple_moving_average, sharpe_ratio, momentum_signal


def test_simulation_growth():
    engine = SimulationEngine("growth")
    result = engine.run(
        initial_state={"population": 100.0, "growth_rate": 0.1},
        step_fn=simple_growth_step,
        n_steps=5,
    )
    assert result.final_state["population"] > 100.0
    assert len(result.steps) == 6


def test_simulation_market():
    engine = SimulationEngine("market")
    result = engine.run(
        initial_state={"price": 100.0, "volatility": 0.01, "regime": "calm"},
        step_fn=nested_market_step,
        n_steps=20,
    )
    assert "price" in result.final_state
    assert len(result.steps) == 21


def test_shannon_entropy():
    h = shannon_entropy([0.5, 0.5])
    assert abs(h - 1.0) < 1e-9


def test_kl_divergence():
    p = normalize([1, 1, 1])
    q = normalize([1, 1, 1])
    assert abs(kl_divergence(p, q)) < 1e-9


def test_cognitive_architecture():
    arch = build_default_architecture()
    summary = arch.summary()
    assert summary["depth"] >= 2
    assert summary["node_count"] >= 7

    def perceive(ctx):
        ctx["perceived"] = True
        return ctx

    arch.on("perceive", perceive)
    out = arch.tick({"sensor": 42})
    assert out.get("perceived") is True


def test_portfolio_and_signals():
    port = Portfolio(cash=10_000)
    port.update("AAPL", 10, 150.0)
    assert port.cash == 10_000 - 1500
    mv = port.market_value({"AAPL": 160.0})
    assert abs(mv - (8500 + 1600)) < 1e-6

    prices = [100, 102, 101, 105, 110, 108, 112]
    sma = simple_moving_average(prices, 3)
    assert len(sma) == len(prices)

    rets = [0.01, -0.005, 0.02, 0.0]
    sr = sharpe_ratio(rets)
    assert isinstance(sr, float)

    mom = momentum_signal(prices, lookback=3)
    assert mom != 0.0
