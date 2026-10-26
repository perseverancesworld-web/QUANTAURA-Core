"""Resonance Bridge: impedance, graph, mechanical topology, and QPIE adapters.

Model boundaries:
- Smith-chart transforms are exact algebra for normalized impedance.
- AC nodal analysis uses declared lumped branch models.
- Complex graph propagation is a separate reduced-order model, not a circuit,
  biological neural model, or quantum model.
- Delaunay adjacency is geometric and is never substituted for mechanical bonds.
- Records do not validate novel physics or authorize real-world actuation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import math
from typing import Any, Iterable, Mapping

import numpy as np

SCHEMA_VERSION = "qpie.resonance-bridge.experiment.v0.2"


def impedance_to_gamma(z_normalized: complex) -> complex:
    """Smith transform: Γ=(z−1)/(z+1), for normalized impedance z."""
    z = complex(z_normalized)
    if not (math.isfinite(z.real) and math.isfinite(z.imag)):
        raise ValueError("Normalized impedance must be finite.")
    if abs(z + 1) < 1e-15:
        raise ValueError("Normalized impedance z=-1 is singular.")
    return (z - 1) / (z + 1)


def gamma_to_impedance(gamma: complex) -> complex:
    """Inverse Smith transform: z=(1+Γ)/(1−Γ)."""
    gamma = complex(gamma)
    if not (math.isfinite(gamma.real) and math.isfinite(gamma.imag)):
        raise ValueError("Reflection coefficient must be finite.")
    if abs(1 - gamma) < 1e-15:
        raise ValueError("Γ=1 maps to infinite impedance.")
    return (1 + gamma) / (1 - gamma)


def smith_metrics(z_normalized: complex) -> dict[str, Any]:
    gamma = impedance_to_gamma(z_normalized)
    magnitude = abs(gamma)
    return {
        "z_normalized": [complex(z_normalized).real, complex(z_normalized).imag],
        "gamma": [gamma.real, gamma.imag],
        "reflection_magnitude": magnitude,
        "return_loss_db": math.inf if magnitude == 0 else -20 * math.log10(magnitude),
        "vswr": math.inf if magnitude >= 1 else (1 + magnitude) / (1 - magnitude),
    }



def smith_chart_grid_data(
    resistance_values: Iterable[float] = (0.0, 0.2, 0.5, 1.0, 2.0, 5.0),
    reactance_values: Iterable[float] = (-5.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 5.0),
    samples: int = 241,
    extent: float = 5.0,
) -> dict[str, Any]:
    """Generate plot-ready Smith-chart loci without a plotting dependency.

    Resistance and reactance are normalized to the reference impedance. The
    generated constant-resistance / constant-reactance samples cover the passive
    half-plane (r >= 0); the unit-circle boundary is returned separately.
    """
    if not isinstance(samples, int) or samples < 2:
        raise ValueError("samples must be an integer >= 2.")
    if not math.isfinite(extent) or extent <= 0:
        raise ValueError("extent must be finite and positive.")
    r_values = [float(value) for value in resistance_values]
    x_values = [float(value) for value in reactance_values]
    if any(not math.isfinite(value) or value < 0 for value in r_values):
        raise ValueError("Normalized resistance values must be finite and nonnegative.")
    if any(not math.isfinite(value) for value in x_values):
        raise ValueError("Normalized reactance values must be finite.")
    x_sweep = np.linspace(-extent, extent, samples)
    r_sweep = np.linspace(0.0, extent, samples)

    def locus(points):
        output = []
        for r, x in points:
            gamma = impedance_to_gamma(complex(float(r), float(x)))
            output.append([float(gamma.real), float(gamma.imag)])
        return output

    constant_resistance = {
        str(r): locus([(r, x) for x in x_sweep]) for r in r_values
    }
    constant_reactance = {
        str(x): locus([(r, x) for r in r_sweep]) for x in x_values
    }
    boundary = [[float(math.cos(t)), float(math.sin(t))]
                for t in np.linspace(0.0, 2.0 * math.pi, samples)]
    return {
        "schema": "qpie.resonance-bridge.smith-grid.v0.1",
        "normalization": "z = R/R_ref + j X/R_ref",
        "constant_resistance": constant_resistance,
        "constant_reactance": constant_reactance,
        "unit_circle_boundary": boundary,
        "samples_per_locus": samples,
        "extent": extent,
        "limitations": ["plot geometry only; not measured data",
                        "resistance curves assume normalized resistance r >= 0"],
    }

def _nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative.")
    return value


@dataclass(frozen=True)
class SeriesRLC:
    """Ideal lumped series RLC branch, SI units; None omits L or C."""
    resistance_ohm: float = 1.0
    inductance_h: float | None = None
    capacitance_f: float | None = None

    def __post_init__(self):
        _nonnegative("resistance_ohm", self.resistance_ohm)
        if self.inductance_h is not None:
            _nonnegative("inductance_h", self.inductance_h)
        if self.capacitance_f is not None:
            _nonnegative("capacitance_f", self.capacitance_f)
        if self.resistance_ohm == 0 and not self.inductance_h and not self.capacitance_f:
            raise ValueError("A zero-valued branch is singular.")

    def impedance(self, frequency_hz: float) -> complex:
        f = float(frequency_hz)
        if not math.isfinite(f) or f < 0:
            raise ValueError("frequency_hz must be finite and nonnegative.")
        omega = 2 * math.pi * f
        z = complex(self.resistance_ohm, omega * (self.inductance_h or 0.0))
        if self.capacitance_f is not None:
            if self.capacitance_f == 0 or omega == 0:
                raise ValueError("Series capacitor is singular at C=0 or f=0.")
            z += 1 / (1j * omega * self.capacitance_f)
        if abs(z) < 1e-15:
            raise ValueError("Branch impedance is zero or singular.")
        return z


@dataclass(frozen=True)
class EdgeElectricalSpec:
    """Series R-L path in parallel with capacitance; an explicit lumped model."""
    resistance_ohm: float = 1.0
    inductance_h: float = 0.0
    capacitance_f: float = 0.0

    def __post_init__(self):
        _nonnegative("resistance_ohm", self.resistance_ohm)
        _nonnegative("inductance_h", self.inductance_h)
        _nonnegative("capacitance_f", self.capacitance_f)
        if self.resistance_ohm == 0 and self.inductance_h == 0:
            raise ValueError("Series R-L path cannot have both R and L equal to zero.")

    def admittance(self, frequency_hz: float) -> complex:
        f = float(frequency_hz)
        if not math.isfinite(f) or f < 0:
            raise ValueError("frequency_hz must be finite and nonnegative.")
        omega = 2 * math.pi * f
        z = complex(self.resistance_ohm, omega * self.inductance_h)
        if abs(z) < 1e-15:
            raise ValueError("Series R-L impedance is singular.")
        return 1 / z + 1j * omega * self.capacitance_f


@dataclass(frozen=True)
class NetworkNode:
    node_id: str
    layer: str = "network"
    shunt_conductance_s: float = 0.0
    shunt_capacitance_f: float = 0.0
    state_capacitance: float = 1.0
    leak: float = 0.0

    def __post_init__(self):
        if not self.node_id:
            raise ValueError("node_id cannot be empty.")
        _nonnegative("shunt_conductance_s", self.shunt_conductance_s)
        _nonnegative("shunt_capacitance_f", self.shunt_capacitance_f)
        if not math.isfinite(self.state_capacitance) or self.state_capacitance <= 0:
            raise ValueError("state_capacitance must be finite and positive.")
        _nonnegative("leak", self.leak)


@dataclass(frozen=True)
class NetworkEdge:
    edge_id: str
    source: str
    target: str
    electrical: EdgeElectricalSpec = field(default_factory=EdgeElectricalSpec)
    coupling_weight: float = 1.0
    phase_rad: float = 0.0
    mechanical_bond_id: str | None = None

    def __post_init__(self):
        if not self.edge_id or not self.source or not self.target or self.source == self.target:
            raise ValueError("Edge identifiers must be nonempty and self-loops are unsupported.")
        _nonnegative("coupling_weight", self.coupling_weight)
        if not math.isfinite(self.phase_rad):
            raise ValueError("phase_rad must be finite.")


@dataclass
class NetworkModel:
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    name: str = "unnamed-network"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self):
        node_ids = [n.node_id for n in self.nodes]
        edge_ids = [e.edge_id for e in self.edges]
        if len(node_ids) != len(set(node_ids)) or len(edge_ids) != len(set(edge_ids)):
            raise ValueError("Node IDs and edge IDs must be unique.")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                raise ValueError(f"Edge {edge.edge_id} references an unknown node.")

    def without_edges(self, edge_ids: Iterable[str]) -> "NetworkModel":
        removed = set(edge_ids)
        unknown = removed - {edge.edge_id for edge in self.edges}
        if unknown:
            raise ValueError(f"Unknown edge IDs: {sorted(unknown)}")
        return NetworkModel(
            list(self.nodes), [e for e in self.edges if e.edge_id not in removed],
            f"{self.name}-faulted", {**self.metadata, "removed_edges": sorted(removed)}
        )


def solve_ac_network(model: NetworkModel, frequency_hz: float,
                     current_injections_a: Mapping[str, complex]) -> dict[str, complex]:
    """Solve the complex nodal-admittance system; singular floating networks raise."""
    model.validate()
    if not math.isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError("frequency_hz must be finite and nonnegative.")
    index = {node.node_id: i for i, node in enumerate(model.nodes)}
    unknown = set(current_injections_a) - set(index)
    if unknown:
        raise ValueError(f"Unknown current-injection nodes: {sorted(unknown)}")
    if not model.nodes:
        return {}
    n, omega = len(model.nodes), 2 * math.pi * frequency_hz
    y = np.zeros((n, n), dtype=np.complex128)
    for node in model.nodes:
        i = index[node.node_id]
        y[i, i] += node.shunt_conductance_s + 1j * omega * node.shunt_capacitance_f
    for edge in model.edges:
        i, j = index[edge.source], index[edge.target]
        adm = edge.electrical.admittance(frequency_hz)
        y[i, i] += adm
        y[j, j] += adm
        y[i, j] -= adm
        y[j, i] -= adm
    current = np.zeros(n, dtype=np.complex128)
    for node_id, value in current_injections_a.items():
        value = complex(value)
        if not (math.isfinite(value.real) and math.isfinite(value.imag)):
            raise ValueError(f"Current injection for {node_id} must be finite.")
        current[index[node_id]] = value
    volts = np.linalg.solve(y, current)
    return {node.node_id: complex(volts[index[node.node_id]]) for node in model.nodes}


def propagate_complex_state(model: NetworkModel, initial_state: Mapping[str, complex],
                            dt: float = 0.01, steps: int = 100) -> list[dict[str, complex]]:
    """Reduced-order complex graph dynamics; not an AC circuit solver or neural model."""
    model.validate()
    if not math.isfinite(dt) or dt <= 0 or not isinstance(steps, int) or steps < 0:
        raise ValueError("dt must be finite and positive; steps must be a nonnegative integer.")
    nodes = {node.node_id: node for node in model.nodes}
    state = {key: complex(initial_state.get(key, 0j)) for key in nodes}
    if any(not math.isfinite(v.real) or not math.isfinite(v.imag) for v in state.values()):
        raise ValueError("Initial state must be finite.")
    history = [dict(state)]
    for _ in range(steps):
        dx = {key: -node.leak * state[key] for key, node in nodes.items()}
        for edge in model.edges:
            phase = complex(math.cos(edge.phase_rad), math.sin(edge.phase_rad))
            flow = edge.coupling_weight * phase * (state[edge.source] - state[edge.target])
            dx[edge.source] -= flow
            dx[edge.target] += flow
        state = {key: state[key] + dt * dx[key] / nodes[key].state_capacitance for key in nodes}
        history.append(dict(state))
    return history


@dataclass(frozen=True)
class MechanicalBond:
    bond_id: str
    node_a: str
    node_b: str
    stiffness: float | None = None
    damping: float | None = None
    material: str | None = None


@dataclass
class MechanicalGraph:
    """Persistent bonds remain separate from positions and geometric adjacency."""
    positions: dict[str, tuple[float, float]]
    bonds: list[MechanicalBond]
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self):
        if not self.positions:
            raise ValueError("Mechanical graph requires positions.")
        for node_id, point in self.positions.items():
            if len(point) != 2 or not all(math.isfinite(float(v)) for v in point):
                raise ValueError(f"Invalid 2D position for {node_id}.")
        ids = [bond.bond_id for bond in self.bonds]
        if len(ids) != len(set(ids)):
            raise ValueError("Mechanical bond IDs must be unique.")
        for bond in self.bonds:
            if bond.node_a not in self.positions or bond.node_b not in self.positions:
                raise ValueError(f"Bond {bond.bond_id} references an unknown node.")
            if bond.node_a == bond.node_b:
                raise ValueError("Mechanical self-bonds are unsupported.")
            for label, value in (("stiffness", bond.stiffness), ("damping", bond.damping)):
                if value is not None and (not math.isfinite(value) or value < 0):
                    raise ValueError(f"{label} must be finite and nonnegative.")

    def without_bonds(self, bond_ids: Iterable[str]) -> "MechanicalGraph":
        removed = set(bond_ids)
        unknown = removed - {b.bond_id for b in self.bonds}
        if unknown:
            raise ValueError(f"Unknown mechanical bond IDs: {sorted(unknown)}")
        return MechanicalGraph(dict(self.positions), [b for b in self.bonds if b.bond_id not in removed],
                              {**self.metadata, "removed_bonds": sorted(removed)})


def delaunay_edges(positions: Mapping[str, tuple[float, float]]) -> set[tuple[str, str]]:
    """Optional SciPy Delaunay geometric neighbors. These are not mechanical bonds."""
    if len(positions) < 3:
        raise ValueError("At least three points are required for 2D Delaunay triangulation.")
    try:
        from scipy.spatial import Delaunay
    except ImportError as exc:
        raise ImportError("delaunay_edges requires SciPy; install quantaura-core[sci].") from exc
    ids = list(positions)
    points = np.asarray([positions[key] for key in ids], dtype=float)
    if points.shape != (len(ids), 2) or not np.isfinite(points).all():
        raise ValueError("Positions must be finite 2D coordinates.")
    edges = set()
    for triangle in Delaunay(points).simplices:
        for i in range(3):
            for j in range(i + 1, 3):
                edges.add(tuple(sorted((ids[int(triangle[i])], ids[int(triangle[j])]))))
    return edges


def mechanical_to_network(graph: MechanicalGraph,
                          electrical_specs: Mapping[str, EdgeElectricalSpec],
                          default_shunt_conductance_s: float = 1e-6) -> NetworkModel:
    """Convert bonds only when a model is explicitly supplied for every bond ID."""
    graph.validate()
    bond_ids = {bond.bond_id for bond in graph.bonds}
    if bond_ids != set(electrical_specs):
        raise ValueError(f"Electrical mapping mismatch: missing={sorted(bond_ids-set(electrical_specs))}, "
                         f"extra={sorted(set(electrical_specs)-bond_ids)}")
    nodes = [NetworkNode(k, layer="mechanical",
                         shunt_conductance_s=default_shunt_conductance_s) for k in graph.positions]
    edges = [NetworkEdge(f"bond:{b.bond_id}", b.node_a, b.node_b, electrical_specs[b.bond_id],
                         mechanical_bond_id=b.bond_id) for b in graph.bonds]
    model = NetworkModel(nodes, edges, "mechanical-electrical-coupling",
                         {"adapter": "mechanical_to_network"})
    model.validate()
    return model


def matched_model_comparison(baseline: NetworkModel, candidate: NetworkModel,
                             tolerance: float = 1e-9) -> dict[str, Any]:
    """Check nodes, topology, budgets, dynamic terms, and declared circuit components."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative.")
    baseline.validate()
    candidate.validate()

    def signature(model):
        return {
            "nodes": sorted(n.node_id for n in model.nodes),
            "topology": sorted(tuple(sorted((e.source, e.target))) for e in model.edges),
            "edge_count": len(model.edges),
            "coupling_budget": sum(e.coupling_weight for e in model.edges),
            "node_parameters": sorted(
                (n.node_id, n.shunt_conductance_s, n.shunt_capacitance_f,
                 n.state_capacitance, n.leak) for n in model.nodes
            ),
            "branch_parameters": sorted(
                (e.edge_id, tuple(sorted((e.source, e.target))),
                 e.electrical.resistance_ohm, e.electrical.inductance_h,
                 e.electrical.capacitance_f) for e in model.edges
            ),
            "dynamic_parameters": sorted(
                (e.edge_id, e.coupling_weight) for e in model.edges
            ),
            "link_phases": sorted(
                (e.edge_id, e.source, e.target, e.phase_rad) for e in model.edges
            ),
        }

    a, b = signature(baseline), signature(candidate)
    flags = {
        "matched_nodes": a["nodes"] == b["nodes"],
        "matched_topology": a["topology"] == b["topology"],
        "matched_edge_count": a["edge_count"] == b["edge_count"],
        "matched_coupling_budget": abs(a["coupling_budget"] - b["coupling_budget"]) <= tolerance,
        "matched_node_parameters": a["node_parameters"] == b["node_parameters"],
        "matched_branch_parameters": a["branch_parameters"] == b["branch_parameters"],
        "matched_dynamic_parameters": a["dynamic_parameters"] == b["dynamic_parameters"],
        "matched_link_phases": a["link_phases"] == b["link_phases"],
    }
    return {
        **flags,
        "matched_except_link_phases": all(
            flags[key] for key in flags if key != "matched_link_phases"
        ),
        "matched_complete_model": all(flags.values()),
        "baseline": a,
        "candidate": b,
        "tolerance": tolerance,
    }

def fault_sensitivity_report(model: NetworkModel, frequency_hz: float,
                             current_injections_a: Mapping[str, complex],
                             observed_node: str) -> dict[str, Any]:
    """Remove each edge in turn and report voltage sensitivity or a singular solve."""
    if observed_node not in {node.node_id for node in model.nodes}:
        raise ValueError(f"Unknown observed node {observed_node}.")
    base = solve_ac_network(model, frequency_hz, current_injections_a)[observed_node]
    rows = []
    for edge in model.edges:
        try:
            value = solve_ac_network(model.without_edges([edge.edge_id]), frequency_hz,
                                     current_injections_a)[observed_node]
            rows.append({"edge_id": edge.edge_id, "status": "solved",
                         "baseline_voltage": [base.real, base.imag],
                         "fault_voltage": [value.real, value.imag],
                         "relative_voltage_change": abs(value-base) / max(abs(base), 1e-15)})
        except np.linalg.LinAlgError:
            rows.append({"edge_id": edge.edge_id, "status": "singular_after_fault",
                         "baseline_voltage": [base.real, base.imag],
                         "fault_voltage": None, "relative_voltage_change": None})
    return {"schema": "qpie.resonance-bridge.fault-report.v0.1", "model": model.name,
            "frequency_hz": float(frequency_hz), "observed_node": observed_node, "rows": rows,
            "limitations": ["linear lumped AC model", "results depend on declared parameters and shunts"]}


def to_physical_state_space(model: NetworkModel, frequency_hz: float = 0.0):
    """Adapt into QPIE's canonical state object; does not create a transition certificate."""
    model.validate()
    from quantaura.qpie.state_space import PhysicalStateSpace, BoundaryConditions
    indices = {node.node_id: i for i, node in enumerate(model.nodes)}
    incidence = np.zeros((len(model.edges), len(model.nodes)), dtype=float)
    admittances = np.asarray([e.electrical.admittance(frequency_hz) for e in model.edges], dtype=complex)
    for k, edge in enumerate(model.edges):
        incidence[k, indices[edge.source]] = -1
        incidence[k, indices[edge.target]] = 1
    return PhysicalStateSpace(
        geometry={"kind": "network_graph", "node_ids": list(indices),
                  "edge_ids": [e.edge_id for e in model.edges]},
        fields={"edge_admittance_real": admittances.real, "edge_admittance_imag": admittances.imag},
        matter={"incidence": incidence},
        topology={"dim": 1, "invariants": {"node_count": len(model.nodes), "edge_count": len(model.edges)}},
        information={"model_name": model.name, "frequency_hz": float(frequency_hz),
                     "mechanical_bond_ids": [e.mechanical_bond_id for e in model.edges]},
        boundary=BoundaryConditions(kind="explicit_shunt_to_ground",
             data={"node_shunts_s": {n.node_id: n.shunt_conductance_s for n in model.nodes}}),
        metadata={"source": "qpie.resonance_bridge", "scientific_status": "CANDIDATE",
                  "model_metadata": dict(model.metadata)},
    )


class EvidenceStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    PERSISTENT = "PERSISTENT"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


def evaluate_promotion_gate(*, requested_status: EvidenceStatus | str, tests_passed: bool,
                            matched_classical_baseline: bool, independent_reproduction: bool = False,
                            human_reviewed: bool = False) -> dict[str, Any]:
    """Fail-closed example gate; not a replacement for the SVE-X registry."""
    status = EvidenceStatus(requested_status)
    requirements = {"tests_passed": bool(tests_passed),
                    "matched_classical_baseline": bool(matched_classical_baseline),
                    "independent_reproduction": bool(independent_reproduction),
                    "human_reviewed": bool(human_reviewed)}
    if status in (EvidenceStatus.VALIDATED, EvidenceStatus.PERSISTENT):
        missing = [key for key, ok in requirements.items() if not ok]
        accepted = not missing
    elif status == EvidenceStatus.EXPERIMENTAL:
        missing = [] if tests_passed else ["tests_passed"]
        accepted = bool(tests_passed)
    else:
        missing, accepted = [], True
    return {"requested_status": status.value, "accepted": accepted,
            "effective_status": status.value if accepted else EvidenceStatus.CANDIDATE.value,
            "missing_requirements": missing, "requirements": requirements,
            "policy": "qpie.resonance-bridge.lifecycle-gate.v0.1"}


def _json_safe(value: Any) -> Any:
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity" if value < 0 else "NaN"
    return value


def make_experiment_record(*, model: NetworkModel, parameters: Mapping[str, Any],
                           results: Mapping[str, Any], metadata: Mapping[str, Any] | None = None,
                           status: EvidenceStatus | str = EvidenceStatus.CANDIDATE) -> dict[str, Any]:
    """Make deterministic JSON-safe experiment metadata; hash is not a signature."""
    model.validate()
    body = {"schema": SCHEMA_VERSION, "status": EvidenceStatus(status).value,
            "model": _json_safe({"name": model.name, "nodes": model.nodes, "edges": model.edges,
                                 "metadata": model.metadata}),
            "parameters": _json_safe(parameters), "results": _json_safe(results),
            "metadata": _json_safe(metadata or {}),
            "limitations": ["results are conditional on declared lumped parameters",
                            "no biological equivalence or quantum advantage is implied",
                            "SHA-256 is an integrity hash, not a digital signature",
                            "the record does not authorize real-world actuation"]}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
    body["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return body
