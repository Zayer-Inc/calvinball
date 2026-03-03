"""Tool: read/write files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file. Creates parent directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write to."},
            "content": {"type": "string", "description": "Content to write."},
        },
        "required": ["path", "content"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            p = Path(kwargs["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(kwargs["content"])
            return ToolResult(output=f"Wrote {len(kwargs['content'])} chars to {p}")
        except Exception as e:
            return ToolResult(output="", error=str(e))


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read."},
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            p = Path(kwargs["path"])
            if not p.exists():
                return ToolResult(output="", error=f"File not found: {p}")
            content = p.read_text()
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(output="", error=str(e))
