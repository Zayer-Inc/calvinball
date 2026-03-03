"""Tool: save learned facts to memory."""

from __future__ import annotations

from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class RememberTool(BaseTool):
    name = "remember"
    description = (
        "Save a learned fact to memory for use in future investigations. "
        "Use this when you discover something useful about the data, schema, "
        "business logic, or domain that would be helpful to remember."
    )
    parameters = {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "The fact to remember.",
            },
        },
        "required": ["fact"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        from calvinball.persistence.memory import save_fact

        fact = kwargs["fact"]
        await save_fact(fact, source="agent")
        return ToolResult(output=f"Remembered: {fact}")
