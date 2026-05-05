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
            "max_tokens": self.max_tokens,
        }
        if _supports_temperature(self.model):
            kwargs["temperature"] = self.temperature
        if tools:
            kwargs["tools"] = tools
        response = await litellm.acompletion(**kwargs)
        return response


def _supports_temperature(model: str) -> bool:
    """Some newer models (e.g. Claude Opus 4.7) reject the temperature param."""
    name = model.lower()
    return "opus-4-7" not in name and "opus-4.7" not in name
