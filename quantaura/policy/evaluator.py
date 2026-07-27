"""Deterministic policy evaluation for intents.

Flags actions that exceed financial thresholds or require human approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class PolicyEngine:
    """Simple rule-based policy engine (v0.1)."""

    def __init__(self) -> None:
        self.rules: dict[str, dict[str, Any]] = {
            "TRANSFER_FUNDS": {"max_amount": 1000.0, "require_human": True},
            "DATABASE_WRITE": {"require_human": False},
            "SIMULATION_RUN": {"require_human": False},
            "QUANT_TRADE": {"max_amount": 5000.0, "require_human": True},
        }

    def evaluate(self, action_type: str, payload: dict) -> PolicyDecision:
        rule = self.rules.get(action_type)
        if not rule:
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason=f"Unknown action type: {action_type}",
            )

        if action_type in ("TRANSFER_FUNDS", "QUANT_TRADE"):
            amount = float(payload.get("amount", 0.0))
            max_amount = float(rule.get("max_amount", 1000.0))

            if amount > max_amount:
                return PolicyDecision(
                    allowed=True,
                    requires_approval=True,
                    reason=(
                        f"Amount (${amount}) exceeds automatic threshold "
                        f"(${max_amount}). Human approval required."
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
