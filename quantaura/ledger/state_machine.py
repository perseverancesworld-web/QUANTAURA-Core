"""Strict linear state machine for intent lifecycle.

No execution occurs without a verified, authorized intent.
Illegal transitions (e.g. COMMITTED → AUTHORIZED) are blocked.
"""

from __future__ import annotations

from enum import Enum


class IntentStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_AUTHORIZATION = "PENDING_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    COMMITTED = "COMMITTED"
    COMPENSATED = "COMPENSATED"
    REJECTED = "REJECTED"


# Valid state transition map — linear & irreversible where required
VALID_TRANSITIONS: dict[IntentStatus, set[IntentStatus]] = {
    IntentStatus.DRAFT: {IntentStatus.PENDING_AUTHORIZATION, IntentStatus.REJECTED},
    IntentStatus.PENDING_AUTHORIZATION: {
        IntentStatus.AUTHORIZED,
        IntentStatus.REJECTED,
    },
    IntentStatus.AUTHORIZED: {IntentStatus.COMMITTED, IntentStatus.COMPENSATED},
    IntentStatus.COMMITTED: {IntentStatus.COMPENSATED},
    IntentStatus.REJECTED: set(),
    IntentStatus.COMPENSATED: set(),
}


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""


def transition_state(
    current_status: IntentStatus, target_status: IntentStatus
) -> IntentStatus:
    """Validate and execute a state transition or raise.

    Raises:
        InvalidStateTransitionError: if the transition is not allowed.
    """
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidStateTransitionError(
            f"Illegal state transition from {current_status.value} to {target_status.value}."
        )
    return target_status
