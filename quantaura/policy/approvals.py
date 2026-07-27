"""Multi-party approval flows.

When an intent reaches PENDING_AUTHORIZATION it may require
N distinct human (or service) approvals before becoming AUTHORIZED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Approval:
    actor: str
    decision: str  # "approve" | "reject"
    comment: str = ""
    timestamp: str = ""


@dataclass
class ApprovalResult:
    complete: bool
    authorized: bool
    reason: str
    approvals: list[dict[str, Any]] = field(default_factory=list)


class ApprovalManager:
    """Tracks and evaluates multi-party approvals for an intent."""

    def add_approval(
        self,
        current_approvals: list[dict[str, Any]],
        required: int,
        actor: str,
        decision: str,
        comment: str = "",
    ) -> ApprovalResult:
        existing_actors = {a.get("actor") for a in current_approvals}
        if actor in existing_actors:
            return ApprovalResult(
                complete=False,
                authorized=False,
                reason=f"Actor '{actor}' has already submitted an approval.",
                approvals=current_approvals,
            )

        entry = {
            "actor": actor,
            "decision": decision,
            "comment": comment,
        }
        updated = current_approvals + [entry]

        if decision == "reject":
            return ApprovalResult(
                complete=True,
                authorized=False,
                reason=f"Rejected by {actor}: {comment or 'no comment'}",
                approvals=updated,
            )

        approved_count = sum(1 for a in updated if a["decision"] == "approve")
        if approved_count >= required:
            return ApprovalResult(
                complete=True,
                authorized=True,
                reason=f"Received {approved_count}/{required} approvals.",
                approvals=updated,
            )

        return ApprovalResult(
            complete=False,
            authorized=False,
            reason=f"Waiting for more approvals ({approved_count}/{required}).",
            approvals=updated,
        )
