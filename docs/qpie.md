# QPIE-27 — QUANTAURA Physical Intelligence Engine

A **computational laboratory for discovering emergent physics** in coupled systems.

PRISM-MATTER is the programmable-material **subsystem**. The central object is not a material — it is a **state-space of physical systems**.

## Layers

| Layer | Module | Role |
|-------|--------|------|
| State-space | `qpie.state_space` | Geometry, fields, matter, topology, information, BC |
| Common geometry | `qpie.geometry` | Shared DEC-oriented representation |
| Gauge | `qpie.gauge` | U(1) links, plaquette holonomy, Wilson action |
| Topology | `qpie.topology` | Hopf / skyrmion discrete proxies |
| Vortex | `qpie.vortex` | Vorticity, helicity |
| Causal physics | `qpie.causal` | `do(X=x)` interventions |
| Transition algebra | `qpie.transition` | Certificates on transitions |
| Discovery objective | `qpie.discovery` | Score informative experiments |
| Firewall | `qpie.firewall` | Tier 0–5; no auto Tier-5 claims |
| Observatory | `qpie.observatory` | Physical-state agents |
| PRISM-MATTER | `qpie.prism` | Material configurations inside state-space |
| Benchmarks | `qpie.benchmarks` | Known-solution calibration |
| Adapters | `qpie.adapters` | Classical (quantum/lab later) |

## Firewall

Simulation anomalies are **never** promoted to “new physics” by the engine. Tier 5 requires human scientific process.

## Quick check

```python
from quantaura.qpie import run_all_benchmarks, LatticeGaugeU1, default_physics_graph

print(run_all_benchmarks())
g = LatticeGaugeU1.zeros(8, 8)
print(g.wilson_action())  # 0.0
print(default_physics_graph().do("geometry", 1.5).observed_effects)
```

## Relation to the Execution Authorization Kernel

QPIE proposes experiments. Fabrication, actuation, and other side effects still require **authorized intents**.
