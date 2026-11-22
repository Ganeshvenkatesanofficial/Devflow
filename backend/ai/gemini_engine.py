"""Google Gemini engine."""

from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from .base import AIEngine


class GeminiEngine(AIEngine):
    """Uses Google Gemini API (Gemini 2.5 Flash, Gemini 2.5 Pro, etc.)."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._api_key = api_key.strip() if api_key else ""
        self._model = model.strip() if model else "gemini-2.5-flash"
        # Google Generative AI provides an OpenAI-compatible endpoint
        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to direct Gemini REST API
            print(f"[GeminiEngine] OpenAI endpoint failed ({e}), trying direct REST API for {self._model}...")
            return await self._generate_rest(prompt, system_prompt)

    async def _generate_rest(self, prompt: str, system_prompt: str = "") -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
        }
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    async def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False
