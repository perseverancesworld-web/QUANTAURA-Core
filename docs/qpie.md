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

## Spectral / resonance bridge

The `quantaura.qpie.spectral` module provides a gauge-covariant Hermitian
operator on periodic 2D lattices, local U(1) gauge transforms, spectral
diagonalization, octave-width log2 grouping, and mechanical stiffness-mode
frequency conversion.

```python
import numpy as np
from quantaura.qpie import LatticeGaugeU1
from quantaura.qpie.spectral import (
    gauge_covariant_hamiltonian,
    hermitian_spectrum,
    octave_histogram,
)

gauge = LatticeGaugeU1.zeros(12, 12)
H = gauge_covariant_hamiltonian(gauge)
spectrum = hermitian_spectrum(H)
print(spectrum.hermitian_residual, spectrum.eigenvalues[:8])
# For measured or physically dimensioned frequencies:
print(octave_histogram(np.array([10.0, 20.0, 40.0]), reference_frequency=10.0))
```

The octave grouping is an analysis convention, not a claim that nature follows
Russell's cosmology. Hamiltonian eigenvalues are not automatically physical Hz.
See [Russell–Tesla–QPIE bridge](russell_tesla_bridge.md) for the evidence ledger,
portfolio mapping, test sequence, and scientific guardrails.

## Durable registry

```bash
export QUANTAURA_QPIE_STORE=/tmp/qpie.sqlite
```

Hypotheses and anomalies persist when a file path is set (default `:memory:`).
