"""Base AI engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIEngine(ABC):
    """Abstract base for all AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine identifier (openai, anthropic, ollama)."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Send a prompt and return the AI response text."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this engine is reachable and configured."""
