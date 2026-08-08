from fastapi.testclient import TestClient

from quantaura.policy.packs import load_policy_pack
from quantaura.policy.evaluator import PolicyEngine
from quantaura.api.main import app


def test_default_pack_has_transfer():
    rules = load_policy_pack("configs/policy_packs/default.yaml")
    assert rules["TRANSFER_FUNDS"]["max_amount"] == 1000.0


def test_enterprise_pack_stricter():
    rules = load_policy_pack("configs/policy_packs/enterprise.yaml")
    assert rules["TRANSFER_FUNDS"]["max_amount"] == 100.0
    assert rules["DATABASE_WRITE"]["require_human"] is True


def test_engine_with_pack():
    eng = PolicyEngine(load_policy_pack("configs/policy_packs/enterprise.yaml"))
    d = eng.evaluate("TRANSFER_FUNDS", {"amount": 50})
    assert d.requires_approval is True


def test_api_key_middleware(monkeypatch):
    monkeypatch.setenv("QUANTAURA_API_KEYS", "secret-demo-key")
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/v1/qpie/dec/status").status_code == 401
    assert client.get("/v1/qpie/dec/status", headers={"X-API-Key": "secret-demo-key"}).status_code == 200
    monkeypatch.delenv("QUANTAURA_API_KEYS", raising=False)
