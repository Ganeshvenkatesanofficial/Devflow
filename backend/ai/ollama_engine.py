"""Ollama local AI engine — runs models on the developer's machine."""

from __future__ import annotations

import httpx

from .base import AIEngine


class OllamaEngine(AIEngine):
    """Uses Ollama for local AI inference. No data leaves the machine."""

    def __init__(self, model: str = "llama3.1", host: str = "http://127.0.0.1:11434"):
        self._model = model
        self._host = host.rstrip("/")

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3},
        }

        hosts = [self._host, "http://127.0.0.1:11434", "http://localhost:11434"]
        last_exc = None
        for h in dict.fromkeys(hosts):
            url = f"{h}/api/chat"
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("message", {}).get("content", "").strip()
            except Exception as e:
                last_exc = e
                continue

        if last_exc:
            raise last_exc
        return ""

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._host}/api/tags")
                if resp.status_code != 200:
                    return False
                models = resp.json().get("models", [])
                return any(m.get("name", "").startswith(self._model) for m in models)
        except Exception:
            return False
