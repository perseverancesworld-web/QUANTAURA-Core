#!/usr/bin/env python3
"""Demo: LangChain-style callable gated by the kernel (no langchain install required)."""

from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient
from quantaura.integrations.langchain_tools import protect_langchain_tool
import httpx

BASE = "http://localhost:8000"


def main() -> None:
    priv, pub = generate_keypair()
    httpx.post(
        f"{BASE}/v1/intents/register-key",
        params={"public_key_hex": pub},
        headers={"X-Tenant-ID": "lc-demo"},
    )
    client = IntentClient(BASE, "lc-demo", priv)

    def send_email(to: str, body: str) -> dict:
        return {"sent": True, "to": to, "body": body}

    gated = protect_langchain_tool(send_email, client=client, action_type="DATABASE_WRITE")
    print(gated(to="ops@example.com", body="kernel allowed this"))


if __name__ == "__main__":
    main()
