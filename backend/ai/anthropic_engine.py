"""Anthropic / Claude engine."""

from __future__ import annotations

import anthropic

from .base import AIEngine


class AnthropicEngine(AIEngine):
    """Uses Anthropic API (Claude)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "anthropic"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        kwargs = {
            "model": self._model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self._client.messages.create(**kwargs)
        return response.content[0].text.strip()

    async def is_available(self) -> bool:
        try:
            # Simple check — a real call would cost tokens
            return bool(self._client.api_key)
        except Exception:
            return False
