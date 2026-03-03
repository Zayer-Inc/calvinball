"""Tool execution engine."""

from __future__ import annotations

import json
import time
from typing import Any

from calvinball.tools.base import ToolResult
from calvinball.tools.registry import ToolRegistry


async def execute_tool_call(
    registry: ToolRegistry,
    tool_name: str,
    arguments: dict[str, Any],
) -> ToolResult:
    """Execute a single tool call and return the result."""
    tool = registry.get(tool_name)
    if tool is None:
        return ToolResult(output="", error=f"Unknown tool: {tool_name}")
    try:
        result = await tool.execute(**arguments)
        return result
    except Exception as e:
        return ToolResult(output="", error=f"Tool execution failed: {e}")
