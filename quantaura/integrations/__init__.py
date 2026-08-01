"""Optional framework integrations (LangChain, etc.)."""

from __future__ import annotations

__all__ = ["protect_langchain_tool"]


def __getattr__(name: str):
    if name == "protect_langchain_tool":
        from quantaura.integrations.langchain_tools import protect_langchain_tool

        return protect_langchain_tool
    raise AttributeError(name)
