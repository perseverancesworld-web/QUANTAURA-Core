"""LangChain / LangGraph tool wrapper that forces every invocation through the kernel.

Install optional extra:
    pip install 'quantaura-core[langchain]'

Usage:
    from quantaura.integrations.langchain_tools import protect_langchain_tool
    from quantaura.sdk.python.client import IntentClient

    client = IntentClient(...)
    tool = protect_langchain_tool(my_tool, client=client, action_type="TRANSFER_FUNDS")
"""

from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def protect_langchain_tool(
    tool: Any,
    *,
    client: Any,
    action_type: str,
    name: Optional[str] = None,
) -> Any:
    """Wrap a LangChain BaseTool (or plain callable) so runs go through IntentClient."""
    if callable(tool) and not hasattr(tool, "invoke") and not hasattr(tool, "_run"):
        return client.protected_action(action_type)(tool)

    try:
        from langchain_core.tools import BaseTool, StructuredTool
    except ImportError as exc:
        raise ImportError(
            "LangChain integration requires langchain-core. "
            "Install with: pip install 'quantaura-core[langchain]'"
        ) from exc

    if isinstance(tool, BaseTool):
        original_run = tool._run
        original_arun = getattr(tool, "_arun", None)

        @client.protected_action(action_type)
        def gated_run(*args: Any, **kwargs: Any) -> Any:
            return original_run(*args, **kwargs)

        tool._run = lambda *a, **k: gated_run(*a, **k)  # type: ignore[method-assign]

        if original_arun is not None:

            async def gated_arun(*args: Any, **kwargs: Any) -> Any:
                @client.protected_action(action_type)
                def _gate() -> None:
                    return None

                _gate()
                return await original_arun(*args, **kwargs)

            tool._arun = gated_arun  # type: ignore[method-assign]

        if name:
            tool.name = name
        return tool

    if callable(tool):
        gated = client.protected_action(action_type)(tool)
        return StructuredTool.from_function(
            func=gated,
            name=name or getattr(tool, "__name__", action_type.lower()),
            description=getattr(tool, "__doc__", None) or f"Kernel-gated {action_type}",
        )

    raise TypeError(f"Unsupported tool type: {type(tool)}")
