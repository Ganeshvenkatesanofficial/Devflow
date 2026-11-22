"""OpenAI / GPT engine."""

from __future__ import annotations

from openai import AsyncOpenAI

from .base import AIEngine


class OpenAIEngine(AIEngine):
    """Uses OpenAI API (GPT-4o, GPT-4, GPT-3.5-turbo)."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    async def is_available(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
