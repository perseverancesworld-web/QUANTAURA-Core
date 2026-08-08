"""PRISM-MATTER — programmable-material subsystem of QPIE-27."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np

from quantaura.qpie.state_space import PhysicalStateSpace, empty_lattice_state


@dataclass
class MaterialConfiguration:
    name: str
    parameters: dict[str, float] = field(default_factory=dict)
    lattice: PhysicalStateSpace | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def default_metamaterial_seed(nx: int = 16, ny: int = 16) -> MaterialConfiguration:
    state = empty_lattice_state((nx, ny))
    state.fields["epsilon"] = np.ones((nx, ny))
    state.matter["fill_fraction"] = np.zeros((nx, ny))
    return MaterialConfiguration(
        name="seed_metamaterial",
        parameters={"target_index": 1.5},
        lattice=state,
        metadata={"subsystem": "PRISM-MATTER"},
    )
