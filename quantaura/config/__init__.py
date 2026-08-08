"""Runtime configuration for multi-tenant / hosted deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> set[str]:
    return {x.strip() for x in value.split(",") if x.strip()}


@dataclass
class Settings:
    allowed_tenants: set[str] = field(default_factory=set)
    require_signature: bool = False
    default_required_approvals: int = 1
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    environment: str = "development"
    api_keys_configured: bool = False
    rate_limit_per_min: int = 0
    policy_pack: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        allowed = _split_csv(os.environ.get("QUANTAURA_ALLOWED_TENANTS", ""))
        require_sig = os.environ.get("QUANTAURA_REQUIRE_SIGNATURE", "").lower() in (
            "1", "true", "yes",
        )
        try:
            defaults = int(os.environ.get("QUANTAURA_DEFAULT_REQUIRED_APPROVALS", "1"))
        except ValueError:
            defaults = 1
        cors = os.environ.get("QUANTAURA_CORS_ORIGINS", "*")
        origins = ["*"] if cors.strip() == "*" else [o.strip() for o in cors.split(",") if o.strip()]
        try:
            rl = int(os.environ.get("QUANTAURA_RATE_LIMIT_PER_MIN", "0"))
        except ValueError:
            rl = 0
        keys = bool(_split_csv(os.environ.get("QUANTAURA_API_KEYS", "")))
        return cls(
            allowed_tenants=allowed,
            require_signature=require_sig,
            default_required_approvals=max(1, defaults),
            cors_origins=origins,
            environment=os.environ.get("QUANTAURA_ENV", "development"),
            api_keys_configured=keys,
            rate_limit_per_min=max(0, rl),
            policy_pack=os.environ.get("QUANTAURA_POLICY_PACK", ""),
        )

    def tenant_allowed(self, tenant_id: str) -> bool:
        if not self.allowed_tenants:
            return True
        return tenant_id in self.allowed_tenants


settings = Settings.from_env()
