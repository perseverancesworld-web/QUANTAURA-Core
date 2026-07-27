"""Nested cognitive architecture scaffold (Fractal Intelligence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import uuid


@dataclass
class CognitiveNode:
    name: str
    level: int = 0
    children: list["CognitiveNode"] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    node_id: str = field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")

    def add_child(self, child: "CognitiveNode") -> "CognitiveNode":
        child.level = self.level + 1
        self.children.append(child)
        return child

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def walk(self) -> list["CognitiveNode"]:
        nodes = [self]
        for c in self.children:
            nodes.extend(c.walk())
        return nodes


class CognitiveArchitecture:
    """Root container for a fractal cognitive tree."""

    def __init__(self, root_name: str = "root") -> None:
        self.root = CognitiveNode(name=root_name, level=0)
        self._hooks: dict[str, list[Callable]] = {
            "perceive": [],
            "deliberate": [],
            "act": [],
        }

    def on(self, phase: str, fn: Callable) -> None:
        if phase not in self._hooks:
            raise ValueError(f"Unknown phase: {phase}")
        self._hooks[phase].append(fn)

    def tick(self, observation: dict[str, Any]) -> dict[str, Any]:
        ctx: dict[str, Any] = {"observation": observation, "nodes": {}}

        for fn in self._hooks["perceive"]:
            ctx = fn(ctx) or ctx

        for fn in self._hooks["deliberate"]:
            ctx = fn(ctx) or ctx

        for fn in self._hooks["act"]:
            ctx = fn(ctx) or ctx

        return ctx

    def summary(self) -> dict[str, Any]:
        return {
            "root": self.root.name,
            "depth": self.root.depth(),
            "node_count": len(self.root.walk()),
            "nodes": [
                {"id": n.node_id, "name": n.name, "level": n.level}
                for n in self.root.walk()
            ],
        }


def build_default_architecture() -> CognitiveArchitecture:
    arch = CognitiveArchitecture("fractal_root")

    perception = arch.root.add_child(CognitiveNode("perception"))
    perception.add_child(CognitiveNode("sensor_fusion"))
    perception.add_child(CognitiveNode("anomaly_detect"))

    deliberation = arch.root.add_child(CognitiveNode("deliberation"))
    deliberation.add_child(CognitiveNode("planning"))
    deliberation.add_child(CognitiveNode("policy_check"))

    action = arch.root.add_child(CognitiveNode("action"))
    action.add_child(CognitiveNode("tool_invocation"))
    action.add_child(CognitiveNode("commitment"))

    return arch
