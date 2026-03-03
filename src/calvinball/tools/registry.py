"""Tool registry — static and hot-loaded tools."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from calvinball.tools.base import BaseTool


class ToolRegistry:
    """Holds all registered tools and provides specs for the LLM."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all_specs(self) -> list[dict[str, Any]]:
        return [t.to_function_spec() for t in self._tools.values()]

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def load_generated_tool(self, path: Path) -> BaseTool | None:
        """Hot-load a Python file that defines a BaseTool subclass."""
        module_name = f"calvinball.generated.{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find the first BaseTool subclass in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseTool)
                and attr is not BaseTool
            ):
                tool = attr()
                self.register(tool)
                return tool
        return None
