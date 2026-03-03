"""Tool: ask the human for clarification."""

from __future__ import annotations

from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class AskHumanTool(BaseTool):
    name = "ask_human"
    description = (
        "Ask the human a question when you're stuck or need clarification. "
        "Use sparingly — only when you genuinely can't proceed without input."
    )
    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask the human.",
            },
        },
        "required": ["question"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()
        question = kwargs["question"]
        console.print(f"\n[bold yellow]Agent needs your input:[/bold yellow]")
        console.print(f"  {question}\n")
        answer = Prompt.ask("[bold]Your answer[/bold]")
        return ToolResult(output=f"Human answered: {answer}")
