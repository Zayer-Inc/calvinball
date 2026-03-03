"""litellm wrapper with async support."""

from __future__ import annotations

from typing import Any

import litellm

from calvinball.config.settings import LLMSettings

# Suppress litellm's verbose logging
litellm.suppress_debug_info = True


class LLMClient:
    """Thin async wrapper around litellm."""

    def __init__(self, settings: LLMSettings) -> None:
        self.model = settings.model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Send a chat completion request. Returns the litellm response."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        response = await litellm.acompletion(**kwargs)
        return response
