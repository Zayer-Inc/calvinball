"""Tool: execute Python code in a sandboxed subprocess."""

from __future__ import annotations

import asyncio
import json
import textwrap
from typing import Any

from calvinball.tools.base import BaseTool, ToolResult


class PythonExecTool(BaseTool):
    name = "python_exec"
    description = (
        "Execute Python code and return the output. "
        "Use this for calculations, data transformations, or any general computation. "
        "The code runs in a subprocess. Print results to stdout."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute. Use print() for output.",
            },
        },
        "required": ["code"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode().strip()
            err = stderr.decode().strip()
            if proc.returncode != 0:
                return ToolResult(output=output, error=err or f"Exit code {proc.returncode}")
            result = output
            if err:
                result += f"\n[stderr]: {err}"
            return ToolResult(output=result or "(no output)")
        except asyncio.TimeoutError:
            return ToolResult(output="", error="Execution timed out after 30 seconds")
        except Exception as e:
            return ToolResult(output="", error=str(e))
