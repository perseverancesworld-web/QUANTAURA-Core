"""Runtime configuration for multi-tenant / hosted deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


def _split_csv(value: str) -> set[str]:
    return {x.strip() for x in value.split(",") if x.strip()}


@dataclass
class Settings:
    """Env-driven settings for hosted / multi-tenant mode.

    QUANTAURA_ALLOWED_TENANTS=tenant-a,tenant-b   (empty = allow all)
    QUANTAURA_REQUIRE_SIGNATURE=true             (force Ed25519 for all tenants)
    QUANTAURA_DEFAULT_REQUIRED_APPROVALS=1
    QUANTAURA_CORS_ORIGINS=*                     (comma-separated)
    """

    allowed_tenants: set[str] = field(default_factory=set)
    require_signature: bool = False
    default_required_approvals: int = 1
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    environment: str = "development"

    @classmethod
    def from_env(cls) -> "Settings":
        allowed = _split_csv(os.environ.get("QUANTAURA_ALLOWED_TENANTS", ""))
        require_sig = os.environ.get("QUANTAURA_REQUIRE_SIGNATURE", "").lower() in (
            "1",
            "true",
            "yes",
        )
        try:
            defaults = int(os.environ.get("QUANTAURA_DEFAULT_REQUIRED_APPROVALS", "1"))
        except ValueError:
            defaults = 1
        cors = os.environ.get("QUANTAURA_CORS_ORIGINS", "*")
        origins = ["*"] if cors.strip() == "*" else [o.strip() for o in cors.split(",") if o.strip()]
        return cls(
            allowed_tenants=allowed,
            require_signature=require_sig,
            default_required_approvals=max(1, defaults),
            cors_origins=origins,
            environment=os.environ.get("QUANTAURA_ENV", "development"),
        )

    def tenant_allowed(self, tenant_id: str) -> bool:
        if not self.allowed_tenants:
            return True
        return tenant_id in self.allowed_tenants


settings = Settings.from_env()
