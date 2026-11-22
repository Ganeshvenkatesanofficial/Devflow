"""AI engine factory — picks the right engine from config."""

from __future__ import annotations

from .base import AIEngine
from .openai_engine import OpenAIEngine
from .anthropic_engine import AnthropicEngine
from .ollama_engine import OllamaEngine
from .gemini_engine import GeminiEngine


def get_engine(config: dict) -> AIEngine:
    """Create an AI engine based on the config's 'ai_provider' field."""
    name = config.get("ai_provider", "ollama").lower()

    if name == "gemini":
        return GeminiEngine(
            api_key=config.get("gemini_api_key", ""),
            model=config.get("gemini_model", "gemini-2.5-flash"),
        )
    elif name == "openai":
        return OpenAIEngine(
            api_key=config.get("openai_api_key", ""),
            model=config.get("openai_model", "gpt-4o"),
        )
    elif name == "anthropic":
        return AnthropicEngine(
            api_key=config.get("anthropic_api_key", ""),
            model=config.get("anthropic_model", "claude-3-5-sonnet-20241022"),
        )
    elif name == "ollama":
        return OllamaEngine(
            model=config.get("ollama_model", "llama3.1"),
            host=config.get("ollama_host", "http://127.0.0.1:11434"),
        )
    else:
        raise ValueError(f"Unknown AI provider: {name!r}. Use 'gemini', 'openai', 'anthropic', or 'ollama'.")
