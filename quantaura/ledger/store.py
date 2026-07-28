"""Durable intent ledger (SQLite).

Process-local default path under /tmp avoids cross-process collisions.
Set QUANTAURA_LEDGER_PATH to override. Use QUANTAURA_LEDGER_BACKEND=postgres for Postgres.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

from quantaura.ledger.state_machine import IntentStatus


def _default_db_path() -> str:
    env = os.environ.get("QUANTAURA_LEDGER_PATH")
    if env == ":memory:":
        return "file:quantaura_mem?mode=memory&cache=shared"
    pid = os.getpid()
    for candidate in (
        env,
        f"/tmp/quantaura_ledger_{pid}.db",
        str(Path.home() / ".quantaura" / f"ledger_{pid}.db"),
        f"quantaura_ledger_{pid}.db",
    ):
        if not candidate:
            continue
        if candidate == ":memory:":
            return "file:quantaura_mem?mode=memory&cache=shared"
        try:
            p = Path(candidate)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a"):
                pass
            return str(p)
        except OSError:
            continue
    return "file:quantaura_mem?mode=memory&cache=shared"


class IntentStore:
    """Thread-safe SQLite-backed intent store."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path) if db_path is not None else _default_db_path()
        self._lock = threading.Lock()
        self._is_memory = self.db_path.startswith("file:") or self.db_path == ":memory:"
        self._mem_conn: sqlite3.Connection | None = None
        if self._is_memory:
            self._mem_conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=30, uri=True
            )
            self._mem_conn.row_factory = sqlite3.Row
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intents (
                    intent_id     TEXT PRIMARY KEY,
                    tenant_id     TEXT NOT NULL,
                    action_type   TEXT NOT NULL,
                    payload_hash  TEXT NOT NULL,
                    status        TEXT NOT NULL,
                    reason        TEXT,
                    payload_json  TEXT NOT NULL,
                    approvals     TEXT DEFAULT '[]',
                    required_approvals INTEGER DEFAULT 1,
                    created_at    TEXT DEFAULT (datetime('now')),
                    updated_at    TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_id     TEXT NOT NULL,
                    event         TEXT NOT NULL,
                    actor         TEXT,
                    detail_json   TEXT,
                    created_at    TEXT DEFAULT (datetime('now'))
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
        with self._lock:
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO intents (
                    intent_id, tenant_id, action_type, payload_hash,
                    status, reason, payload_json, approvals, required_approvals
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(intent_id) DO UPDATE SET
                    status = excluded.status,
                    reason = excluded.reason,
                    approvals = excluded.approvals,
                    required_approvals = excluded.required_approvals,
                    updated_at = datetime('now')
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
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM intents WHERE intent_id = ?", (intent_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_for_tenant(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM intents WHERE tenant_id = ? ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def append_audit(
        self, intent_id: str, event: str, actor: str = "", detail: Optional[dict] = None
    ) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO audit_log (intent_id, event, actor, detail_json)
                VALUES (?, ?, ?, ?)
                """,
                (intent_id, event, actor, json.dumps(detail or {})),
            )
            conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "intent_id": row["intent_id"],
            "tenant_id": row["tenant_id"],
            "action_type": row["action_type"],
            "payload_hash": row["payload_hash"],
            "status": row["status"],
            "reason": row["reason"],
            "payload": json.loads(row["payload_json"]),
            "approvals": json.loads(row["approvals"] or "[]"),
            "required_approvals": row["required_approvals"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


store = IntentStore()
