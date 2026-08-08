"""Physical state-space X — the central object of QPIE.

X = { geometry, fields, matter, topology, information, boundary conditions }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class BoundaryConditions:
    kind: str = "periodic"
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhysicalStateSpace:
    """State-space of a coupled physical system (not a single material)."""

    geometry: dict[str, Any] = field(default_factory=dict)
    fields: dict[str, np.ndarray] = field(default_factory=dict)
    matter: dict[str, np.ndarray] = field(default_factory=dict)
    topology: dict[str, Any] = field(default_factory=dict)
    information: dict[str, Any] = field(default_factory=dict)
    boundary: BoundaryConditions = field(default_factory=BoundaryConditions)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "geometry_keys": list(self.geometry.keys()),
            "fields": {k: list(v.shape) for k, v in self.fields.items()},
            "matter": {k: list(v.shape) for k, v in self.matter.items()},
            "topology": self.topology,
            "boundary": self.boundary.kind,
            "metadata": self.metadata,
        }


def empty_lattice_state(
    shape: tuple[int, ...] = (16, 16),
    spacing: float = 1.0,
) -> PhysicalStateSpace:
    dims = len(shape)
    return PhysicalStateSpace(
        geometry={
            "kind": "regular_lattice",
            "shape": shape,
            "spacing": spacing,
            "dim": dims,
        },
        fields={},
        matter={},
        topology={"dim": dims, "invariants": {}},
        information={"observers": []},
        boundary=BoundaryConditions(kind="periodic"),
        metadata={"source": "empty_lattice_state"},
    )
