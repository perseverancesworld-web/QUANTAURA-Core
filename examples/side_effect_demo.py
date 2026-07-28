#!/usr/bin/env python3
"""Demo: real side effect only after kernel authorization.

Writes a row to a local SQLite 'effects' table — but only if the
Execution Authorization Kernel authorizes the intent.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient
import httpx

BASE = "http://localhost:8000"
DB = Path("/tmp/quantaura_effects.db")


def ensure_effects_table() -> None:
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS effects (id INTEGER PRIMARY KEY, msg TEXT, at TEXT DEFAULT (datetime('now')))"
    )
    conn.commit()
    conn.close()


def main() -> None:
    ensure_effects_table()
    print("=== Side-effect demo (kernel-gated write) ===\n")

    priv, pub = generate_keypair()
    httpx.post(
        f"{BASE}/v1/intents/register-key",
        params={"public_key_hex": pub},
        headers={"X-Tenant-ID": "effect-agent"},
    )

    client = IntentClient(BASE, "effect-agent", priv)

    @client.protected_action("DATABASE_WRITE")
    def write_effect(msg: str) -> dict:
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO effects (msg) VALUES (?)", (msg,))
        conn.commit()
        conn.close()
        return {"written": True, "msg": msg, "db": str(DB)}

    result = write_effect(msg="hello from authorized agent")
    print(f"Result: {result}")

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, msg, at FROM effects").fetchall()
    conn.close()
    print(f"Effects table rows: {rows}")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
