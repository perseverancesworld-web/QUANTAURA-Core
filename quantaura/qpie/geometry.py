"""Common geometric representation for coupled physics (DEC-oriented)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import numpy as np


class FormDegree(str, Enum):
    ZERO = "0-form"
    ONE = "1-form"
    TWO = "2-form"
    VOLUME = "volume-form"


@dataclass
class GeometricField:
    name: str
    degree: FormDegree
    values: np.ndarray
    units: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommonGeometry:
    shape: tuple[int, ...]
    spacing: float = 1.0
    metric_scale: float = 1.0
    fields: dict[str, GeometricField] = field(default_factory=dict)

    @property
    def dim(self) -> int:
        return len(self.shape)

    def n_cells(self) -> int:
        n = 1
        for s in self.shape:
            n *= s
        return int(n)

    def attach(self, name: str, degree: FormDegree, values: np.ndarray, units: str = "") -> None:
        self.fields[name] = GeometricField(name=name, degree=degree, values=values, units=units)


def regular_grid_2d(nx: int = 16, ny: int = 16, spacing: float = 1.0) -> CommonGeometry:
    return CommonGeometry(shape=(nx, ny), spacing=spacing)
