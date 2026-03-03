"""Message history and context management."""

from __future__ import annotations

from typing import Any


class MessageHistory:
    """Manages the LLM conversation message list."""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self.messages: list[dict[str, Any]] = []

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, message: dict[str, Any]) -> None:
        """Add a raw assistant message (may contain tool_calls)."""
        self.messages.append(message)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self.messages.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )

    def to_api_messages(self) -> list[dict[str, Any]]:
        return [{"role": "system", "content": self.system_prompt}] + self.messages

    def serializable(self) -> list[dict[str, Any]]:
        """Return messages in a JSON-serializable form."""
        return list(self.messages)

    @classmethod
    def from_saved(cls, system_prompt: str, messages: list[dict[str, Any]]) -> MessageHistory:
        h = cls(system_prompt)
        h.messages = list(messages)
        return h
