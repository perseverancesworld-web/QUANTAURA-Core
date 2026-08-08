"""Physical-state agents N_i = (x_i, S_i, O_i, C_i)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class PhysicalStateAgent:
    agent_id: str
    location: tuple[float, ...] | str
    local_state: dict[str, Any] = field(default_factory=dict)
    observations: list[dict[str, Any]] = field(default_factory=list)
    causal_links: list[str] = field(default_factory=list)
    role: str = "cell"

    @classmethod
    def create(
        cls,
        role: str = "cell",
        location: tuple[float, ...] | str = (0.0,),
        **state: Any,
    ) -> "PhysicalStateAgent":
        return cls(
            agent_id=f"N_{uuid.uuid4().hex[:8]}",
            location=location,
            local_state=dict(state),
            role=role,
        )


@dataclass
class Observatory:
    agents: dict[str, PhysicalStateAgent] = field(default_factory=dict)

    def register(self, agent: PhysicalStateAgent) -> str:
        self.agents[agent.agent_id] = agent
        return agent.agent_id

    def observe(self, agent_id: str, payload: dict[str, Any]) -> None:
        self.agents[agent_id].observations.append(payload)

    def by_role(self, role: str) -> list[PhysicalStateAgent]:
        return [a for a in self.agents.values() if a.role == role]

    def size(self) -> int:
        return len(self.agents)
