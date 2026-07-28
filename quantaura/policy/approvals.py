"""Multi-party approval manager with roles and timeouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional


@dataclass
class ApprovalResult:
    approvals: list[dict[str, Any]]
    complete: bool
    authorized: bool
    reason: str
    expired: bool = False


@dataclass
class RolePolicy:
    """Required roles and minimum distinct actors."""

    required_roles: set[str] = field(default_factory=set)
    min_actors: int = 1
    timeout_seconds: int = 3600


DEFAULT_ROLE_POLICY = RolePolicy(required_roles=set(), min_actors=1, timeout_seconds=3600)


class ApprovalManager:
    """Collects approve/reject votes; supports roles and expiry."""

    def __init__(self, policy: Optional[RolePolicy] = None) -> None:
        self.policy = policy or DEFAULT_ROLE_POLICY

    def add_approval(
        self,
        current_approvals: list[dict[str, Any]],
        required: int,
        actor: str,
        decision: str,
        comment: str = "",
        role: str = "",
        created_at: Optional[str] = None,
    ) -> ApprovalResult:
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - created
                if age > timedelta(seconds=self.policy.timeout_seconds):
                    return ApprovalResult(
                        approvals=current_approvals,
                        complete=True,
                        authorized=False,
                        reason=f"Intent expired after {self.policy.timeout_seconds}s",
                        expired=True,
                    )
            except ValueError:
                pass

        for a in current_approvals:
            if a.get("actor") == actor:
                return ApprovalResult(
                    approvals=current_approvals,
                    complete=False,
                    authorized=False,
                    reason=f"Actor {actor} already voted",
                )

        entry = {
            "actor": actor,
            "decision": decision,
            "comment": comment,
            "role": role,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        approvals = list(current_approvals) + [entry]

        if decision == "reject":
            return ApprovalResult(
                approvals=approvals,
                complete=True,
                authorized=False,
                reason=f"Rejected by {actor}" + (f" ({role})" if role else ""),
            )

        if self.policy.required_roles:
            approved_roles = {
                a.get("role") for a in approvals if a.get("decision") == "approve" and a.get("role")
            }
            missing = self.policy.required_roles - approved_roles
            if missing:
                return ApprovalResult(
                    approvals=approvals,
                    complete=False,
                    authorized=False,
                    reason=f"Waiting for roles: {', '.join(sorted(missing))}",
                )

        approve_count = sum(1 for a in approvals if a.get("decision") == "approve")
        min_needed = max(required, self.policy.min_actors)

        if approve_count >= min_needed:
            return ApprovalResult(
                approvals=approvals,
                complete=True,
                authorized=True,
                reason=f"Authorized with {approve_count} approval(s)",
            )

        return ApprovalResult(
            approvals=approvals,
            complete=False,
            authorized=False,
            reason=f"{approve_count}/{min_needed} approvals collected",
        )
