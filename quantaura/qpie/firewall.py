"""Known-physics firewall: Tier 0–5; never auto-claim new physics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class DiscoveryTier(IntEnum):
    ARTIFACT = 0
    KNOWN_REDISCOVERY = 1
    KNOWN_UNUSUAL = 2
    UNEXPECTED_COUPLING = 3
    ROBUST_UNEXPLAINED = 4
    POTENTIAL_NEW_LAW = 5


@dataclass
class FirewallVerdict:
    tier: DiscoveryTier
    rationale: str
    requires_experiment: bool
    blocks_claim: bool

    @property
    def label(self) -> str:
        return {
            0: "Tier 0 — numerical artifact",
            1: "Tier 1 — known physics rediscovered",
            2: "Tier 2 — known phenomenon, unusual configuration",
            3: "Tier 3 — unexpected coupling (investigate)",
            4: "Tier 4 — robust unexplained experimental result",
            5: "Tier 5 — potential new physical law/model",
        }[int(self.tier)]


def classify_candidate(
    *,
    residual: float,
    matches_known_solution: bool,
    reproduced_across_backends: int = 1,
    has_lab_measurement: bool = False,
    conservation_ok: bool = True,
    notes: str = "",
) -> FirewallVerdict:
    if not conservation_ok or residual > 1e-2:
        return FirewallVerdict(
            DiscoveryTier.ARTIFACT,
            rationale=notes or "Large residual or conservation failure",
            requires_experiment=False,
            blocks_claim=True,
        )
    if matches_known_solution:
        return FirewallVerdict(
            DiscoveryTier.KNOWN_REDISCOVERY,
            rationale=notes or "Matches known analytical/numerical solution",
            requires_experiment=False,
            blocks_claim=False,
        )
    if reproduced_across_backends >= 2 and not has_lab_measurement:
        return FirewallVerdict(
            DiscoveryTier.UNEXPECTED_COUPLING,
            rationale=notes or "Cross-backend signal without lab confirmation",
            requires_experiment=True,
            blocks_claim=True,
        )
    if has_lab_measurement and reproduced_across_backends >= 2:
        return FirewallVerdict(
            DiscoveryTier.ROBUST_UNEXPLAINED,
            rationale=notes or "Lab + multi-backend; still not a new law claim",
            requires_experiment=True,
            blocks_claim=True,
        )
    return FirewallVerdict(
        DiscoveryTier.KNOWN_UNUSUAL,
        rationale=notes or "Default conservative tier",
        requires_experiment=False,
        blocks_claim=False,
    )


def assert_not_new_physics(verdict: FirewallVerdict) -> None:
    if verdict.tier >= DiscoveryTier.POTENTIAL_NEW_LAW:
        raise RuntimeError(
            "QPIE firewall: automatic Tier 5 claims are forbidden. "
            "Human review and external validation required."
        )
