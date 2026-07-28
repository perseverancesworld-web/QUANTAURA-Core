"""Postgres IntentStore backend (optional dependency: psycopg[binary]).

Set QUANTAURA_LEDGER_BACKEND=postgres and DATABASE_URL=postgresql://...
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from quantaura.ledger.state_machine import IntentStatus


class PostgresIntentStore:
    """Postgres-backed durable intent store."""

    def __init__(self, dsn: str | None = None) -> None:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise ImportError(
                "Postgres backend requires psycopg. Install with: pip install 'psycopg[binary]'"
            ) from exc

        self._psycopg = psycopg
        self._dict_row = dict_row
        self.dsn = dsn or os.environ.get("DATABASE_URL", "")
        if not self.dsn:
            raise ValueError("DATABASE_URL or dsn required for PostgresIntentStore")
        self._init_schema()

    def _connect(self):
        return self._psycopg.connect(self.dsn, row_factory=self._dict_row)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intents (
                    intent_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    payload_json JSONB NOT NULL DEFAULT '{}',
                    approvals JSONB NOT NULL DEFAULT '[]',
                    required_approvals INTEGER DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    actor TEXT,
                    detail_json JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            conn.commit()

    def save(self, record: dict[str, Any]) -> None:
        status_val = (
            record["status"].value
            if isinstance(record["status"], IntentStatus)
            else record["status"]
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO intents (
                    intent_id, tenant_id, action_type, payload_hash,
                    status, reason, payload_json, approvals, required_approvals
                ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                ON CONFLICT (intent_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    reason = EXCLUDED.reason,
                    approvals = EXCLUDED.approvals,
                    required_approvals = EXCLUDED.required_approvals,
                    updated_at = NOW()
                """,
                (
                    record["intent_id"],
                    record["tenant_id"],
                    record["action_type"],
                    record["payload_hash"],
                    status_val,
                    record.get("reason", ""),
                    json.dumps(record.get("payload", {})),
                    json.dumps(record.get("approvals", [])),
                    record.get("required_approvals", 1),
                ),
            )
            conn.commit()

    def get(self, intent_id: str) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM intents WHERE intent_id = %s", (intent_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_for_tenant(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM intents WHERE tenant_id = %s ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def append_audit(
        self, intent_id: str, event: str, actor: str = "", detail: Optional[dict] = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (intent_id, event, actor, detail_json)
                VALUES (%s, %s, %s, %s::jsonb)
                """,
                (intent_id, event, actor, json.dumps(detail or {})),
            )
            conn.commit()

    @staticmethod
    def _row_to_dict(row: dict) -> dict[str, Any]:
        payload = row["payload_json"]
        approvals = row["approvals"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if isinstance(approvals, str):
            approvals = json.loads(approvals)
        return {
            "intent_id": row["intent_id"],
            "tenant_id": row["tenant_id"],
            "action_type": row["action_type"],
            "payload_hash": row["payload_hash"],
            "status": row["status"],
            "reason": row["reason"],
            "payload": payload or {},
            "approvals": approvals or [],
            "required_approvals": row["required_approvals"],
            "created_at": str(row.get("created_at", "")),
            "updated_at": str(row.get("updated_at", "")),
        }


def get_store():
    """Factory: postgres if configured, else SQLite."""
    backend = os.environ.get("QUANTAURA_LEDGER_BACKEND", "sqlite").lower()
    if backend == "postgres":
        return PostgresIntentStore()
    from quantaura.ledger.store import IntentStore

    return IntentStore()
