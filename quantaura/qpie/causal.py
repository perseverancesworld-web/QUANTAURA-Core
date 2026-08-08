"""Physical causal graph — interventions do(X=x)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import copy


@dataclass
class CausalNode:
    name: str
    domain: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalEdge:
    source: str
    target: str
    mechanism: str = ""
    weight: float = 1.0


@dataclass
class InterventionResult:
    intervened: str
    value: Any
    before: dict[str, Any]
    after: dict[str, Any]
    observed_effects: dict[str, Any]


class CausalPhysicsGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, CausalNode] = {}
        self.edges: list[CausalEdge] = []
        self._propagators: dict[tuple[str, str], Callable[[Any], Any]] = {}

    def add_node(self, node: CausalNode) -> None:
        self.nodes[node.name] = node

    def add_edge(
        self,
        source: str,
        target: str,
        mechanism: str = "",
        weight: float = 1.0,
        propagator: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.edges.append(CausalEdge(source, target, mechanism, weight))
        if propagator is not None:
            self._propagators[(source, target)] = propagator

    def do(self, variable: str, value: Any) -> InterventionResult:
        if variable not in self.nodes:
            raise KeyError(f"Unknown variable: {variable}")
        before = {n: copy.deepcopy(self.nodes[n].value) for n in self.nodes}
        self.nodes[variable].value = value
        effects: dict[str, Any] = {}
        for e in self.edges:
            if e.source != variable:
                continue
            prop = self._propagators.get((e.source, e.target))
            if prop is not None:
                new_val = prop(value)
            else:
                cur = self.nodes[e.target].value
                if isinstance(cur, (int, float)) and isinstance(value, (int, float)):
                    new_val = cur + e.weight * value
                else:
                    new_val = value
            self.nodes[e.target].value = new_val
            effects[e.target] = new_val
        after = {n: copy.deepcopy(self.nodes[n].value) for n in self.nodes}
        return InterventionResult(
            intervened=variable,
            value=value,
            before=before,
            after=after,
            observed_effects=effects,
        )


def default_physics_graph() -> CausalPhysicsGraph:
    g = CausalPhysicsGraph()
    for name, domain, val in [
        ("geometry", "geometry", 1.0),
        ("em", "em", 0.0),
        ("phase", "phase", 0.0),
        ("mechanics", "mechanics", 0.0),
        ("thermal", "thermal", 0.0),
        ("density", "density", 1.0),
        ("vortex", "vortex", 0.0),
        ("topology", "topology", 0.0),
        ("global_state", "global", 0.0),
    ]:
        g.add_node(CausalNode(name=name, domain=domain, value=val))

    def scale(w: float):
        return lambda x: w * float(x)

    g.add_edge("geometry", "em", "metric->Maxwell", 0.5, scale(0.5))
    g.add_edge("geometry", "phase", "metric->gauge", 0.3, scale(0.3))
    g.add_edge("geometry", "mechanics", "metric->stress", 0.4, scale(0.4))
    g.add_edge("em", "thermal", "Joule", 0.2, scale(0.2))
    g.add_edge("phase", "thermal", "dissipation", 0.1, scale(0.1))
    g.add_edge("mechanics", "thermal", "viscous", 0.15, scale(0.15))
    g.add_edge("density", "thermal", "eos", 0.1, scale(0.05))
    g.add_edge("thermal", "vortex", "buoyancy-coupling", 0.25, scale(0.25))
    g.add_edge("vortex", "topology", "linking", 0.5, scale(0.5))
    g.add_edge("topology", "global_state", "aggregate", 1.0, scale(1.0))
    return g
