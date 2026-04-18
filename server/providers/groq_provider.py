"""Groq API provider (OpenAI-compatible)."""

from server.providers.base import ModelInfo
from server.providers.openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    """Groq API provider."""

    name = "groq"
    display_name = "Groq"

    BASE_URL = "https://api.groq.com/openai/v1"

    AVAILABLE_MODELS = [
        ModelInfo(id="llama-3.3-70b-versatile", name="Llama 3.3 70B", provider="groq", context_length=131072),
        ModelInfo(id="mixtral-8x7b-32768", name="Mixtral 8x7B", provider="groq", context_length=32768),
        ModelInfo(id="gemma2-9b-it", name="Gemma 2 9B", provider="groq", context_length=8192),
    ]

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key)

    async def list_models(self):
        return list(self.AVAILABLE_MODELS)
