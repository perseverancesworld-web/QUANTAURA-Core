"""Integration tests against the FastAPI app."""

from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from quantaura.api.main import app
from quantaura.crypto.signatures import generate_keypair, canonicalize_payload

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "quantaura-core"
    assert data["status"] == "ok"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_create_intent_auto_authorized():
    resp = client.post(
        "/v1/intents",
        json={"action_type": "DATABASE_WRITE", "payload": {"table": "ledger"}},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "AUTHORIZED"
    assert "intent_id" in data


def test_create_intent_pending():
    resp = client.post(
        "/v1/intents",
        json={"action_type": "TRANSFER_FUNDS", "payload": {"amount": 50}},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING_AUTHORIZATION"


def test_create_intent_rejected():
    resp = client.post(
        "/v1/intents",
        json={"action_type": "UNKNOWN_ACTION", "payload": {}},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "REJECTED"


def test_state_transition():
    create = client.post(
        "/v1/intents",
        json={"action_type": "DATABASE_WRITE", "payload": {}},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    intent_id = create.json()["intent_id"]
    trans = client.post(
        f"/v1/intents/{intent_id}/transition",
        json={"target_status": "COMMITTED"},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    assert trans.status_code == 200
    assert trans.json()["status"] == "COMMITTED"


def test_illegal_transition_returns_409():
    create = client.post(
        "/v1/intents",
        json={"action_type": "DATABASE_WRITE", "payload": {}},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    intent_id = create.json()["intent_id"]
    trans = client.post(
        f"/v1/intents/{intent_id}/transition",
        json={"target_status": "DRAFT"},
        headers={"X-Tenant-ID": "tenant-demo"},
    )
    assert trans.status_code == 409


def test_signed_intent_flow():
    private_hex, public_hex = generate_keypair()
    reg = client.post(
        "/v1/intents/register-key",
        params={"public_key_hex": public_hex},
        headers={"X-Tenant-ID": "signed-tenant"},
    )
    assert reg.status_code == 200
    payload = {"amount": 10, "to": "alice"}
    sk = SigningKey(bytes.fromhex(private_hex))
    sig = sk.sign(canonicalize_payload(payload)).signature.hex()
    resp = client.post(
        "/v1/intents",
        json={"action_type": "DATABASE_WRITE", "payload": payload},
        headers={
            "X-Tenant-ID": "signed-tenant",
            "X-QUANTAURA-Signature": sig,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "AUTHORIZED"
