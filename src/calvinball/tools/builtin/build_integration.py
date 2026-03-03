"""Meta-tool: agent writes new integration tools at runtime."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from calvinball.config.settings import GENERATED_TOOLS_DIR, Settings
from calvinball.tools.base import BaseTool, ToolResult

_INTEGRATION_PROMPT = """\
You are a Python code generator. Write a single Python file that defines a tool \
for the Calvinball data analyst agent.

The tool must:
1. Import and subclass `calvinball.tools.base.BaseTool`
2. Define `name`, `description`, `parameters` (JSON Schema), and `async execute(**kwargs) -> ToolResult`
3. Import ToolResult from `calvinball.tools.base`
4. Be self-contained (can import standard library and installed packages)
5. Handle errors gracefully and return ToolResult with error info

The tool should: {description}

Requirements/context: {requirements}

Return ONLY the Python code, no markdown fences or explanation.
"""


class BuildIntegrationTool(BaseTool):
    name = "build_integration"
    description = (
        "Meta-tool: generate a new tool/integration by describing what it should do. "
        "The agent writes Python code, validates it, and registers it for immediate use. "
        "Use this when you need a capability that doesn't exist yet (e.g., CSV reader, API connector)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "tool_description": {
                "type": "string",
                "description": "What the tool should do (e.g., 'Read and query CSV files').",
            },
            "requirements": {
                "type": "string",
                "description": "Any specific requirements or context for the tool.",
            },
        },
        "required": ["tool_description"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        description = kwargs["tool_description"]
        requirements = kwargs.get("requirements", "")

        try:
            # Nested LLM call to generate the code
            settings = Settings.load()
            import litellm

            prompt = _INTEGRATION_PROMPT.format(
                description=description, requirements=requirements
            )

            response = await litellm.acompletion(
                model=settings.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4096,
            )

            code = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:])
                if code.endswith("```"):
                    code = code[:-3].strip()

            # Write to disk
            GENERATED_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
            tool_id = uuid.uuid4().hex[:8]
            file_path = GENERATED_TOOLS_DIR / f"tool_{tool_id}.py"
            file_path.write_text(code)

            # Validate by importing
            module_name = f"calvinball.generated.tool_{tool_id}"
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec is None or spec.loader is None:
                file_path.unlink()
                return ToolResult(output="", error="Failed to create module spec")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find the tool class
            tool_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                ):
                    tool_cls = attr
                    break

            if tool_cls is None:
                file_path.unlink()
                return ToolResult(output="", error="Generated code did not define a BaseTool subclass")

            tool = tool_cls()

            return ToolResult(
                output=(
                    f"Successfully created tool '{tool.name}'!\n"
                    f"Description: {tool.description}\n"
                    f"File: {file_path}\n"
                    f"The tool is now available for use."
                ),
                artifacts={"tool_name": tool.name, "file_path": str(file_path)},
            )
        except Exception as e:
            return ToolResult(output="", error=f"Failed to build integration: {e}")
