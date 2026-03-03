"""BaseTool ABC and ToolResult."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""

    output: str
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)  # file paths, chart data, etc.

    @property
    def success(self) -> bool:
        return self.error is None

    def to_content(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        return self.output


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...

    def to_function_spec(self) -> dict[str, Any]:
        """Return the OpenAI-style function spec for litellm."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
