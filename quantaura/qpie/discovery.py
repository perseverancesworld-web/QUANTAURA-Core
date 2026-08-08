"""Active discovery objective J = aA + bI + gC + dT - lE - mR."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExperimentScore:
    anomaly: float = 0.0
    information_gain: float = 0.0
    cross_domain: float = 0.0
    topological: float = 0.0
    cost: float = 0.0
    risk: float = 0.0
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    delta: float = 1.0
    lamb: float = 0.5
    mu: float = 0.5

    def value(self) -> float:
        return (
            self.alpha * self.anomaly
            + self.beta * self.information_gain
            + self.gamma * self.cross_domain
            + self.delta * self.topological
            - self.lamb * self.cost
            - self.mu * self.risk
        )


def score_experiment(
    *,
    anomaly: float,
    information_gain: float,
    cross_domain: float,
    topological: float,
    cost: float,
    risk: float,
) -> ExperimentScore:
    return ExperimentScore(
        anomaly=anomaly,
        information_gain=information_gain,
        cross_domain=cross_domain,
        topological=topological,
        cost=cost,
        risk=risk,
    )
