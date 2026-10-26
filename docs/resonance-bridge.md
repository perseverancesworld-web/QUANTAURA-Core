# Resonance Bridge (QPIE)

Resonance Bridge connects Smith-chart impedance mathematics to a graph-network model and explicit adapters for persistent mechanical topology.

## Scientific boundaries

- `impedance_to_gamma` and `gamma_to_impedance` implement normalized-impedance reflection transforms.
- `SeriesRLC` and `EdgeElectricalSpec` are idealized lumped models, not universal material laws.
- `solve_ac_network` performs complex nodal analysis with explicit node shunts. An ungrounded singular network raises an error rather than silently adding a fictional ground path.
- `propagate_complex_state` is a separate reduced-order complex graph model. Its phase parameter is not a claim about an ordinary passive circuit or biological neural dynamics.
- `MechanicalGraph` stores persistent bonds separately from positions. `delaunay_edges` computes geometric neighbors only. `mechanical_to_network` requires an explicitly defined electrical specification for every bond and never guesses an impedance from distance.
- `to_physical_state_space` adapts the model to QPIE's canonical state object and marks its status `CANDIDATE`. It does not create a transition certificate.
- Experiment records use a SHA-256 content hash, not a digital signature and not an authorization token.

## Quick start

```python
from quantaura.qpie.resonance_bridge import (
    EdgeElectricalSpec, NetworkEdge, NetworkModel, NetworkNode, solve_ac_network,
)

model = NetworkModel(
    name="two-node-demo",
    nodes=[
        NetworkNode("source", shunt_conductance_s=1e-3),
        NetworkNode("load", shunt_conductance_s=1e-3),
    ],
    edges=[NetworkEdge("bond-01", "source", "load", EdgeElectricalSpec(10.0, 1e-3, 1e-9))],
)
voltages = solve_ac_network(model, 100_000, {"source": 1e-3 + 0j})
print(voltages)
```

## Reproducible checks

```bash
pytest -q tests/test_qpie_resonance_bridge.py
```

## Integration map

- **PRISM-MATTER / Delaunay mesh:** use triangulation for geometry and neighborhood queries; use persistent mechanical bonds for actual load paths, damage, and actuation constraints.
- **QPIE:** use `to_physical_state_space` for its canonical state container. The existing transition-certificate and known-physics firewall mechanisms remain authoritative.
- **QUANTAURA Intent Kernel / Intent Ledger:** simulation functions have no side effects. Any real-world actuation must separately pass the kernel's authorization path.
- **SVE-X lifecycle:** `evaluate_promotion_gate` is a local fail-closed example requiring tests, a matched classical baseline, independent reproduction, and human review for `VALIDATED` / `PERSISTENT`. It is not a replacement for an external SVE-X registry.
- **Quantum research:** a quantum-coupling backend would be a separate adapter. A quantum-advantage claim requires matched classical nonlinear baselines and reproducible metrics.

## Next validation milestones

1. Compare the AC solver to hand-derived two-node circuits and an independent circuit solver.
2. Run edge-failure sweeps with identical source conditions and declared material models.
3. Compare geometric-neighbor changes against mechanical-bond failure without conflating the two graphs.
4. Establish matched classical baselines before making claims about phase effects, quantum coupling, or emergent dynamics.

## Matched-budget controller benchmark

`run_controller_benchmark` compares three one-step kinematic controllers on a fixed node set:

1. Global gradient: each node uses its own residual plus global mean residual information.
2. Local geometric neighbor: each node uses neighbors from Delaunay adjacency (or explicit geometric edges).
3. Topology-aware local: each node uses persistent mechanical bonds, weighted by declared bond stiffness.

Each controller receives the same targets, initial positions, and total displacement budget. That budget is the sum of Euclidean displacement magnitudes, not force, energy, or a complete actuator model. The output includes each command, predicted positions, pre/post RMSE, budget consumed, and limitations. This is a controlled baseline, not a full dynamic mechanics solver.

Run both test groups:

```bash
pytest -q tests/test_qpie_resonance_bridge.py tests/test_qpie_resonance_bridge_control.py
```

## Hermitian graph operator and gauge invariance

The separate quantum-math adapter builds a dense tight-binding-style graph Hamiltonian from the explicit graph topology and link phases. Its convention is:

`H[source,target] = -t exp(+i phi)`; the reverse link is the complex conjugate. Local basis changes use `H' = U H U†`, with `U_ii = exp(i theta_i)`.

The adapter checks Hermiticity, performs dense exact diagonalization for small graphs, and tests whether the eigenvalue spectrum is invariant under the local basis transformation. This provides a reproducible discrete-operator / U(1)-style gauge check related mathematically to QPIE's lattice-gauge work. It is not a quantum-hardware simulator, does not prove coupling to a physical device, and makes no quantum-advantage claim.

Example:

```python
from quantaura.qpie import (
    build_graph_hamiltonian,
    diagonalize_graph_hamiltonian,
    gauge_invariance_report,
)

operator = build_graph_hamiltonian(network_model)
spectrum = diagonalize_graph_hamiltonian(operator)
report = gauge_invariance_report(operator, {"node-0": 0.3, "node-1": -0.2})
assert report["passed"]
```

## Integrated smoke-test example

Run the synthetic, no-side-effect example to exercise the layers together:

```bash
python examples/resonance_bridge_demo.py > resonance_bridge_record.json
```

The record includes AC node voltages, a 50-ohm-reference Smith-chart point, edge-fault sensitivity, matched-budget controller results, a small graph-Hamiltonian spectrum, a gauge-invariance report, model parameters, limitations, and a SHA-256 hash. All inputs are synthetic; the record is marked CANDIDATE.
