"""Matched-budget controllers for the QPIE Resonance Bridge benchmark.

The benchmark uses predicted position updates on a fixed node set. The budget is
the sum of per-node Euclidean displacement magnitudes, not energy or force.
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping

from quantaura.qpie.resonance_bridge import MechanicalGraph, delaunay_edges


def _mean(vectors: list[tuple[float, float]], weights: list[float] | None = None) -> tuple[float, float]:
    if not vectors:
        return (0.0, 0.0)
    if weights is None:
        weights = [1.0] * len(vectors)
    total = sum(weights)
    if total <= 0:
        return (0.0, 0.0)
    return (
        sum(v[0] * w for v, w in zip(vectors, weights)) / total,
        sum(v[1] * w for v, w in zip(vectors, weights)) / total,
    )


def _neighbors_from_edges(node_ids: set[str], edges: Iterable[tuple[str, str]]) -> dict[str, list[str]]:
    neighbors = {node_id: set() for node_id in node_ids}
    for a, b in edges:
        if a not in node_ids or b not in node_ids or a == b:
            raise ValueError(f"Invalid geometric edge {(a, b)}.")
        neighbors[a].add(b)
        neighbors[b].add(a)
    return {key: sorted(value) for key, value in neighbors.items()}


def _rmse(positions: Mapping[str, tuple[float, float]],
          targets: Mapping[str, tuple[float, float]]) -> float:
    if not positions:
        return 0.0
    return math.sqrt(sum(
        (positions[key][0] - targets[key][0]) ** 2 +
        (positions[key][1] - targets[key][1]) ** 2
        for key in positions
    ) / len(positions))


def run_controller_benchmark(
    graph: MechanicalGraph,
    target_positions: Mapping[str, tuple[float, float]],
    total_displacement_budget: float,
    geometric_edges: Iterable[tuple[str, str]] | None = None,
) -> dict:
    """Compare global, geometric-neighbor, and mechanical-topology-aware controllers.

    All controllers receive identical initial positions, targets, node set, and
    total displacement budget. The geometric neighbor controller uses Delaunay
    adjacency unless explicit geometric edges are supplied. The topology-aware
    controller uses persistent mechanical bonds weighted by their declared
    stiffness (or 1.0 if stiffness is unspecified).

    This is a one-step kinematic baseline, not a full mass-spring simulation.
    It does not model force, time, actuator saturation by node, or energy. The
    budget has units of summed coordinate displacement in the positions' units.
    """
    graph.validate()
    budget = float(total_displacement_budget)
    if not math.isfinite(budget) or budget < 0:
        raise ValueError("total_displacement_budget must be finite and nonnegative.")
    node_ids = set(graph.positions)
    if set(target_positions) != node_ids:
        missing, extra = node_ids - set(target_positions), set(target_positions) - node_ids
        raise ValueError(f"Target IDs must match graph nodes; missing={sorted(missing)}, extra={sorted(extra)}")
    targets = {}
    for node_id, point in target_positions.items():
        if len(point) != 2 or not all(math.isfinite(float(v)) for v in point):
            raise ValueError(f"Invalid target position for {node_id}.")
        targets[node_id] = (float(point[0]), float(point[1]))
    positions = {key: (float(p[0]), float(p[1])) for key, p in graph.positions.items()}
    errors = {key: (targets[key][0] - positions[key][0], targets[key][1] - positions[key][1])
              for key in positions}
    global_error = _mean(list(errors.values()))

    if geometric_edges is None:
        geo_edges = delaunay_edges(graph.positions)
    else:
        geo_edges = set(tuple(edge) for edge in geometric_edges)
    geo_neighbors = _neighbors_from_edges(node_ids, geo_edges)

    mechanical_neighbors: dict[str, list[tuple[str, float]]] = {key: [] for key in node_ids}
    for bond in graph.bonds:
        weight = float(bond.stiffness) if bond.stiffness is not None else 1.0
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"Invalid stiffness on bond {bond.bond_id}.")
        mechanical_neighbors[bond.node_a].append((bond.node_b, weight))
        mechanical_neighbors[bond.node_b].append((bond.node_a, weight))

    raw_commands: dict[str, dict[str, tuple[float, float]]] = {
        "global_gradient": {},
        "local_geometric_neighbor": {},
        "topology_aware_local": {},
    }
    for node_id in sorted(node_ids):
        ex, ey = errors[node_id]
        # The global baseline has global residual information available.
        raw_commands["global_gradient"][node_id] = (ex + 0.25 * global_error[0],
                                                     ey + 0.25 * global_error[1])
        # Geometric neighborhoods use Delaunay edges, not persistent bonds.
        geometric_residual = _mean([errors[n] for n in geo_neighbors[node_id]])
        raw_commands["local_geometric_neighbor"][node_id] = (
            ex + 0.5 * geometric_residual[0], ey + 0.5 * geometric_residual[1])
        # Mechanical neighborhoods use actual bonds and their declared stiffnesses.
        pairs = mechanical_neighbors[node_id]
        mechanical_residual = _mean([errors[n] for n, _ in pairs], [w for _, w in pairs])
        raw_commands["topology_aware_local"][node_id] = (
            ex + 0.5 * mechanical_residual[0], ey + 0.5 * mechanical_residual[1])

    results = {}
    for controller, raw in raw_commands.items():
        raw_total = sum(math.hypot(dx, dy) for dx, dy in raw.values())
        scale = (budget / raw_total) if raw_total > 1e-15 else 0.0
        commands = {key: (raw[key][0] * scale, raw[key][1] * scale) for key in sorted(node_ids)}
        predicted = {key: (positions[key][0] + commands[key][0],
                           positions[key][1] + commands[key][1]) for key in sorted(node_ids)}
        consumed = sum(math.hypot(dx, dy) for dx, dy in commands.values())
        results[controller] = {
            "commands": {key: [value[0], value[1]] for key, value in commands.items()},
            "predicted_positions": {key: [value[0], value[1]] for key, value in predicted.items()},
            "rmse_before": _rmse(positions, targets),
            "rmse_after": _rmse(predicted, targets),
            "total_displacement_consumed": consumed,
            "displacement_budget": budget,
            "budget_respected": consumed <= budget + 1e-9,
        }

    return {
        "schema": "qpie.resonance-bridge.controller-benchmark.v0.1",
        "budget_definition": "sum of per-node Euclidean displacement magnitudes; not energy",
        "node_ids": sorted(node_ids),
        "geometric_edge_count": len(geo_edges),
        "mechanical_bond_count": len(graph.bonds),
        "fixed_topology_during_controller_step": True,
        "controllers": results,
        "limitations": [
            "single-step kinematic model",
            "no forces, inertial dynamics, local actuator saturation, or energy accounting",
            "Delaunay edges represent geometry, not mechanical bonds",
            "better result on one benchmark is not proof of general superiority",
        ],
    }
