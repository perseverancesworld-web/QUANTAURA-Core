"""Active experiment selection: max expected information gain / cost."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class ExperimentCandidate:
    experiment_id: str
    expected_info_gain: float
    cost: float
    risk: float = 0.0

    def score(self, lamb: float = 1.0) -> float:
        denom = self.cost + lamb * self.risk
        if denom <= 0:
            return float("inf") if self.expected_info_gain > 0 else 0.0
        return self.expected_info_gain / denom


def select_next_experiment(
    candidates: Iterable[ExperimentCandidate],
    lamb: float = 1.0,
) -> Optional[ExperimentCandidate]:
    items = list(candidates)
    if not items:
        return None
    return max(items, key=lambda c: c.score(lamb))
