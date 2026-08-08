"""Deterministic policy evaluation for intents — pack-driven."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantaura.policy.packs import load_policy_pack


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class PolicyEngine:
    def __init__(self, rules: dict[str, dict[str, Any]] | None = None) -> None:
        self.rules: dict[str, dict[str, Any]] = rules if rules is not None else load_policy_pack()

    def reload(self) -> None:
        self.rules = load_policy_pack()

    def evaluate(self, action_type: str, payload: dict) -> PolicyDecision:
        rule = self.rules.get(action_type)
        if not rule:
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason=f"Unknown action type: {action_type}",
            )
        if "max_amount" in rule:
            amount = float(payload.get("amount", 0.0))
            max_amount = float(rule.get("max_amount", 1000.0))
            if amount > max_amount:
                return PolicyDecision(
                    allowed=True,
                    requires_approval=True,
                    reason=(
                        f"Amount ({amount}) exceeds automatic threshold "
                        f"({max_amount}). Human approval required."
                    ),
                )
        if rule.get("require_human", False):
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                reason=f"Action '{action_type}' requires human approval by policy.",
            )
        return PolicyDecision(
            allowed=True,
            requires_approval=False,
            reason="Passed automatic policy guardrails.",
        )
