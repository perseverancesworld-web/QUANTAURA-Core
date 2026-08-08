"""Durable scientific ledger: hashed evidence records."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Optional


def _hash_payload(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class EvidenceRecord:
    evidence_id: str
    kind: str
    hypothesis_id: str = ""
    run_id: str = ""
    solver: str = ""
    solver_version: str = "qpie-0.5"
    payload: dict[str, Any] = field(default_factory=dict)
    payload_hash: str = ""
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(cls, kind: str, payload: dict[str, Any], **kwargs: Any) -> "EvidenceRecord":
        return cls(
            evidence_id=f"E_{uuid.uuid4().hex[:12]}",
            kind=kind,
            payload=payload,
            payload_hash=_hash_payload(payload),
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScientificLedger:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.environ.get("QUANTAURA_SCI_LEDGER", ":memory:")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS evidence (
                  evidence_id TEXT PRIMARY KEY, kind TEXT, hypothesis_id TEXT, run_id TEXT,
                  solver TEXT, solver_version TEXT, payload_json TEXT, payload_hash TEXT, created_at REAL)"""
            )
            self._conn.commit()

    def append(self, record: EvidenceRecord) -> str:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    record.evidence_id, record.kind, record.hypothesis_id, record.run_id,
                    record.solver, record.solver_version, json.dumps(record.payload),
                    record.payload_hash, record.created_at,
                ),
            )
            self._conn.commit()
        return record.evidence_id

    def list(self, kind: Optional[str] = None) -> list[dict[str, Any]]:
        with self._lock:
            if kind:
                rows = self._conn.execute(
                    "SELECT * FROM evidence WHERE kind=? ORDER BY created_at DESC", (kind,)
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM evidence ORDER BY created_at DESC").fetchall()
        return [
            {
                "evidence_id": r["evidence_id"], "kind": r["kind"], "hypothesis_id": r["hypothesis_id"],
                "run_id": r["run_id"], "solver": r["solver"], "solver_version": r["solver_version"],
                "payload": json.loads(r["payload_json"]), "payload_hash": r["payload_hash"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]


sci_ledger = ScientificLedger()
