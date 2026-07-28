"""Tests for multi-party approval flows and durable store."""

from fastapi.testclient import TestClient

from quantaura.api.main import app
from quantaura.ledger.store import IntentStore
from quantaura.policy.approvals import ApprovalManager

client = TestClient(app)


def test_approval_manager_basic():
    mgr = ApprovalManager()
    r1 = mgr.add_approval([], required=2, actor="alice", decision="approve")
    assert r1.complete is False
    r2 = mgr.add_approval(r1.approvals, required=2, actor="bob", decision="approve")
    assert r2.complete is True
    assert r2.authorized is True


def test_approval_manager_reject():
    mgr = ApprovalManager()
    r = mgr.add_approval([], required=2, actor="alice", decision="reject", comment="too risky")
    assert r.complete is True
    assert r.authorized is False


def test_approval_manager_double_vote():
    mgr = ApprovalManager()
    r1 = mgr.add_approval([], required=2, actor="alice", decision="approve")
    r2 = mgr.add_approval(r1.approvals, required=2, actor="alice", decision="approve")
    assert "already voted" in r2.reason.lower()


def test_api_multi_party_approval():
    create = client.post(
        "/v1/intents",
        json={
            "action_type": "TRANSFER_FUNDS",
            "payload": {"amount": 50},
            "required_approvals": 2,
        },
        headers={"X-Tenant-ID": "tenant-multi"},
    )
    assert create.status_code == 201
    data = create.json()
    assert data["status"] == "PENDING_AUTHORIZATION"
    intent_id = data["intent_id"]

    a1 = client.post(
        f"/v1/intents/{intent_id}/approve",
        json={"decision": "approve", "comment": "looks good"},
        headers={"X-Tenant-ID": "tenant-multi", "X-Actor": "alice"},
    )
    assert a1.status_code == 200
    assert a1.json()["status"] == "PENDING_AUTHORIZATION"

    a2 = client.post(
        f"/v1/intents/{intent_id}/approve",
        json={"decision": "approve"},
        headers={"X-Tenant-ID": "tenant-multi", "X-Actor": "bob"},
    )
    assert a2.status_code == 200
    assert a2.json()["status"] == "AUTHORIZED"


def test_durable_store_roundtrip(tmp_path):
    db = tmp_path / "test.db"
    s = IntentStore(db_path=db)
    record = {
        "intent_id": "req_test123",
        "tenant_id": "t1",
        "action_type": "DATABASE_WRITE",
        "payload_hash": "abc",
        "status": "AUTHORIZED",
        "reason": "ok",
        "payload": {"k": 1},
        "approvals": [],
        "required_approvals": 1,
    }
    s.save(record)
    loaded = s.get("req_test123")
    assert loaded is not None
    assert loaded["tenant_id"] == "t1"
    assert loaded["payload"]["k"] == 1
