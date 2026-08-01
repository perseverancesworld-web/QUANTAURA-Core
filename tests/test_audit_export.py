from fastapi.testclient import TestClient

from quantaura.api.main import app

client = TestClient(app)


def test_audit_json_and_csv():
    create = client.post(
        "/v1/intents",
        json={"action_type": "DATABASE_WRITE", "payload": {"msg": "x"}},
        headers={"X-Tenant-ID": "audit-tenant"},
    )
    assert create.status_code == 201

    j = client.get("/v1/intents/audit", headers={"X-Tenant-ID": "audit-tenant"})
    assert j.status_code == 200
    body = j.json()
    assert body["count"] >= 1
    assert any(e["event"] == "created" for e in body["events"])

    csv_resp = client.get(
        "/v1/intents/audit?format=csv", headers={"X-Tenant-ID": "audit-tenant"}
    )
    assert csv_resp.status_code == 200
    assert "intent_id" in csv_resp.text
    assert "created" in csv_resp.text


def test_tenant_allowlist_blocks():
    from quantaura.config import Settings

    s = Settings(allowed_tenants={"only-this"})
    assert s.tenant_allowed("only-this")
    assert not s.tenant_allowed("other")
