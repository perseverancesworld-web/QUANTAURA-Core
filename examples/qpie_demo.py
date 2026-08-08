#!/usr/bin/env python3
"""End-to-end QPIE demo: DEC, gauge, Schwinger ED, firewall, active select."""

from quantaura.qpie import LatticeGaugeU1, run_all_benchmarks, classify_candidate
from quantaura.qpie.dec import GridComplex2D
from quantaura.qpie.schwinger import exact_spectrum
from quantaura.qpie.active import ExperimentCandidate, select_next_experiment
from quantaura.qpie.adapters.vqe import classical_variational_stub
from quantaura.qpie.hypothesis import Hypothesis
from quantaura.qpie.store.sqlite_registry import SQLiteHypothesisStore


def main() -> None:
    print("=== benchmarks ===")
    for r in run_all_benchmarks():
        print(r)

    c = GridComplex2D(6, 6)
    residual = abs((c.incidence_d1() @ c.incidence_d0()).max())
    print(f"DEC d2 residual: {residual}")

    print("Wilson flat:", LatticeGaugeU1.zeros(8, 8).wilson_action())
    spec = exact_spectrum(3, m=0.4, h=0.1)
    print("Schwinger ED ground:", spec.ground_energy, "gap:", spec.gap)

    vqe = classical_variational_stub(3, m=0.4, h=0.1)
    print("VQE stub:", vqe.to_dict())

    verdict = classify_candidate(
        residual=1e-9, matches_known_solution=True, conservation_ok=True
    )
    print("Firewall:", verdict.label)

    best = select_next_experiment(
        [
            ExperimentCandidate("wilson_scan", 0.3, cost=1.0),
            ExperimentCandidate("ed_spectrum", 1.2, cost=2.0, risk=0.1),
        ]
    )
    print("Next experiment:", best)

    store = SQLiteHypothesisStore(":memory:")
    h = Hypothesis.create("Gap increases with staggered mass m", predicted_observables=["gap"])
    store.save_hypothesis(h)
    print("Stored hypotheses:", store.list_hypotheses())


if __name__ == "__main__":
    main()
