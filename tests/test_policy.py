"""Tests for the policy engine."""

from quantaura.policy.evaluator import PolicyEngine


def test_unknown_action_rejected():
    engine = PolicyEngine()
    decision = engine.evaluate("LAUNCH_MISSILES", {})
    assert decision.allowed is False
    assert "Unknown" in decision.reason


def test_small_transfer_auto_approved():
    engine = PolicyEngine()
    decision = engine.evaluate("TRANSFER_FUNDS", {"amount": 50.0})
    assert decision.allowed is True
    assert decision.requires_approval is True


def test_large_transfer_requires_approval():
    engine = PolicyEngine()
    decision = engine.evaluate("TRANSFER_FUNDS", {"amount": 5000.0})
    assert decision.allowed is True
    assert decision.requires_approval is True
    assert "exceeds" in decision.reason.lower()


def test_database_write_auto():
    engine = PolicyEngine()
    decision = engine.evaluate("DATABASE_WRITE", {"table": "users"})
    assert decision.allowed is True
    assert decision.requires_approval is False
