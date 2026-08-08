"""THEORY	o MEASURE telemetry: manifests, sensors, provenance."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import time
import uuid
import json


def new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


@dataclass
class SensorReading:
    sensor_id: str
    quantity: str
    value: float
    unit: str = ""
    uncertainty: float = 0.0
    timestamp: float = field(default_factory=time.time)
    calibration_id: str = ""


@dataclass
class ExperimentManifest:
    run_id: str
    title: str
    hypothesis_id: str = ""
    model_version: str = "qpie-0.4"
    solver: str = ""
    discretization: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    simulation_outputs: dict[str, Any] = field(default_factory=dict)
    measurements: list[SensorReading] = field(default_factory=list)
    conservation_residuals: dict[str, float] = field(default_factory=dict)
    benchmark_status: str = "unverified"
    notes: str = ""

    def add_measurement(self, reading: SensorReading) -> None:
        self.measurements.append(reading)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def pair_sim_and_measure(
    manifest: ExperimentManifest,
    sim_key: str,
    sensor_quantity: str,
) -> dict[str, Any]:
    sim_val = manifest.simulation_outputs.get(sim_key)
    matches = [m for m in manifest.measurements if m.quantity == sensor_quantity]
    return {
        "run_id": manifest.run_id,
        "sim_key": sim_key,
        "sim_value": sim_val,
        "n_measurements": len(matches),
        "measurement_mean": float(sum(m.value for m in matches) / len(matches)) if matches else None,
        "measurement_uncertainties": [m.uncertainty for m in matches],
    }
