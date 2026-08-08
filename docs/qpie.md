# QPIE — Physical Intelligence Engine

Computational laboratory for **coupled physical systems**. PRISM-MATTER is a material subsystem inside the state-space.

## Invariants

1. **Mathematical:** DEC incidence satisfies d1 d0 = 0 on the grid complex.
2. **Scientific:** Firewall never auto-assigns Tier 5 ("new physical law").
3. **Operational:** Side effects still require the **Execution Authorization Kernel**.

## Quick checks

```python
from quantaura.qpie import run_all_benchmarks, LatticeGaugeU1
from quantaura.qpie.dec import GridComplex2D
from quantaura.qpie.schwinger import exact_spectrum

print(run_all_benchmarks())
c = GridComplex2D(6, 6)
assert abs((c.incidence_d1() @ c.incidence_d0()).max()) < 1e-12
print(exact_spectrum(3).gap)
```

```bash
python examples/qpie_demo.py
curl localhost:8000/v1/qpie/benchmarks
```

## Durable registry

```bash
export QUANTAURA_QPIE_STORE=/tmp/qpie.sqlite
```

Hypotheses and anomalies persist when a file path is set (default `:memory:`).
