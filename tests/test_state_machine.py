"""Tests for the intent state machine."""

import pytest

from quantaura.ledger.state_machine import (
    IntentStatus,
    InvalidStateTransitionError,
    transition_state,
)


def test_valid_happy_path():
    status = IntentStatus.DRAFT
    status = transition_state(status, IntentStatus.PENDING_AUTHORIZATION)
    status = transition_state(status, IntentStatus.AUTHORIZED)
    status = transition_state(status, IntentStatus.COMMITTED)
    status = transition_state(status, IntentStatus.COMPENSATED)
    assert status == IntentStatus.COMPENSATED


def test_auto_authorize_path():
    status = IntentStatus.DRAFT
    status = transition_state(status, IntentStatus.PENDING_AUTHORIZATION)
    status = transition_state(status, IntentStatus.AUTHORIZED)
    assert status == IntentStatus.AUTHORIZED


def test_illegal_transition_raises():
    with pytest.raises(InvalidStateTransitionError):
        transition_state(IntentStatus.COMMITTED, IntentStatus.AUTHORIZED)
    with pytest.raises(InvalidStateTransitionError):
        transition_state(IntentStatus.REJECTED, IntentStatus.AUTHORIZED)
    with pytest.raises(InvalidStateTransitionError):
        transition_state(IntentStatus.DRAFT, IntentStatus.COMMITTED)


def test_terminal_states_have_no_exits():
    for terminal in (IntentStatus.REJECTED, IntentStatus.COMPENSATED):
        with pytest.raises(InvalidStateTransitionError):
            transition_state(terminal, IntentStatus.DRAFT)
