"""Durable hypothesis / anomaly registry (SQLite)."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Optional

from quantaura.qpie.hypothesis import Anomaly, Hypothesis


class SQLiteHypothesisStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.environ.get("QUANTAURA_QPIE_STORE", ":memory:")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS hypotheses (
                  hypothesis_id TEXT PRIMARY KEY,
                  payload_json TEXT NOT NULL,
                  created_at REAL
                );
                CREATE TABLE IF NOT EXISTS anomalies (
                  anomaly_id TEXT PRIMARY KEY,
                  payload_json TEXT NOT NULL,
                  created_at REAL
                );
                """
            )
            self._conn.commit()

    def save_hypothesis(self, h: Hypothesis) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO hypotheses(hypothesis_id, payload_json, created_at) VALUES (?,?,?)",
                (h.hypothesis_id, json.dumps(h.to_dict()), h.created_at),
            )
            self._conn.commit()

    def get_hypothesis(self, hid: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT payload_json FROM hypotheses WHERE hypothesis_id=?", (hid,)
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def list_hypotheses(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT payload_json FROM hypotheses ORDER BY created_at DESC"
            ).fetchall()
        return [json.loads(r["payload_json"]) for r in rows]

    def save_anomaly(self, a: Anomaly) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO anomalies(anomaly_id, payload_json, created_at) VALUES (?,?,?)",
                (a.anomaly_id, json.dumps(a.to_dict()), 0.0),
            )
            self._conn.commit()

    def list_anomalies(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT payload_json FROM anomalies").fetchall()
        return [json.loads(r["payload_json"]) for r in rows]


store = SQLiteHypothesisStore()
