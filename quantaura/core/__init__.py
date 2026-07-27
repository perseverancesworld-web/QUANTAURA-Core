"""Core simulation, math models, cognitive architecture, and quant primitives."""

from .simulation import SimulationEngine, simple_growth_step, nested_market_step
from .math_models import shannon_entropy, kl_divergence, fractal_dimension_boxcount
from .cognitive import CognitiveArchitecture, CognitiveNode, build_default_architecture
from .quant import Portfolio, simple_moving_average, sharpe_ratio, momentum_signal

__all__ = [
    "SimulationEngine",
    "simple_growth_step",
    "nested_market_step",
    "shannon_entropy",
    "kl_divergence",
    "fractal_dimension_boxcount",
    "CognitiveArchitecture",
    "CognitiveNode",
    "build_default_architecture",
    "Portfolio",
    "simple_moving_average",
    "sharpe_ratio",
    "momentum_signal",
]
