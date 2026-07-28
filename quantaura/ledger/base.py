"""Intent store interface — swap SQLite / Postgres without changing callers."""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class IntentStoreProtocol(Protocol):
    def save(self, record: dict[str, Any]) -> None: ...
    def get(self, intent_id: str) -> Optional[dict[str, Any]]: ...
    def list_for_tenant(self, tenant_id: str) -> list[dict[str, Any]]: ...
    def append_audit(
        self, intent_id: str, event: str, actor: str = "", detail: Optional[dict] = None
    ) -> None: ...
