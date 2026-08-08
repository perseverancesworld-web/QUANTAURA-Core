"""Load policy packs from YAML (or built-in defaults)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "TRANSFER_FUNDS": {"max_amount": 1000.0, "require_human": True},
    "DATABASE_WRITE": {"require_human": False},
    "SIMULATION_RUN": {"require_human": False},
    "QUANT_TRADE": {"max_amount": 5000.0, "require_human": True},
    "AGENT_TOOL_CALL": {"require_human": False},
}


def _parse_simple_yaml_actions(text: str) -> dict[str, dict[str, Any]]:
    rules: dict[str, dict[str, Any]] = {}
    current: str | None = None
    in_actions = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.strip() == "actions:":
            in_actions = True
            continue
        if not in_actions:
            continue
        if not line.startswith(" ") and not line.startswith("\t"):
            in_actions = line.strip() == "actions:"
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            current = stripped[:-1]
            rules[current] = {}
            continue
        if current and ":" in stripped:
            k, v = stripped.split(":", 1)
            k, v = k.strip(), v.strip()
            if v.lower() in ("true", "yes"):
                rules[current][k] = True
            elif v.lower() in ("false", "no"):
                rules[current][k] = False
            else:
                try:
                    rules[current][k] = float(v)
                except ValueError:
                    rules[current][k] = v
    return rules


def load_policy_pack(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    pack_path = path or os.environ.get("QUANTAURA_POLICY_PACK", "")
    if not pack_path:
        return dict(DEFAULT_RULES)
    p = Path(pack_path)
    if not p.is_file():
        alt = Path(__file__).resolve().parents[2] / "configs" / "policy_packs" / pack_path
        if alt.is_file():
            p = alt
        else:
            return dict(DEFAULT_RULES)
    text = p.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
        actions = data.get("actions") or {}
        return {str(k): dict(v) for k, v in actions.items()}
    return _parse_simple_yaml_actions(text) or dict(DEFAULT_RULES)
