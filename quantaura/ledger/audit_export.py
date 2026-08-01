"""Audit log export helpers (CSV / JSON) for compliance and design partners."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from quantaura.ledger.store import IntentStore


def list_audit_rows(store: IntentStore, tenant_id: str) -> list[dict[str, Any]]:
    """Return audit events for all intents belonging to a tenant."""
    intents = store.list_for_tenant(tenant_id)
    intent_ids = {i["intent_id"] for i in intents}
    if not intent_ids:
        return []

    rows: list[dict[str, Any]] = []
    with store._lock:
        conn = store._connect()
        cur = conn.execute(
            "SELECT id, intent_id, event, actor, detail_json, created_at FROM audit_log ORDER BY id ASC"
        )
        for r in cur.fetchall():
            if r["intent_id"] not in intent_ids:
                continue
            detail = r["detail_json"]
            if isinstance(detail, str):
                try:
                    detail = json.loads(detail) if detail else {}
                except json.JSONDecodeError:
                    detail = {"raw": detail}
            rows.append(
                {
                    "id": r["id"],
                    "intent_id": r["intent_id"],
                    "event": r["event"],
                    "actor": r["actor"] or "",
                    "detail": detail or {},
                    "created_at": r["created_at"],
                }
            )
    return rows


def audit_to_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["id", "intent_id", "event", "actor", "detail", "created_at"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "id": row["id"],
                "intent_id": row["intent_id"],
                "event": row["event"],
                "actor": row["actor"],
                "detail": json.dumps(row.get("detail") or {}),
                "created_at": row["created_at"],
            }
        )
    return buf.getvalue()
