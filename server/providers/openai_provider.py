"""OpenAI API provider."""

from server.providers.base import ModelInfo
from server.providers.openai_compatible import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI API provider."""

    name = "openai"
    display_name = "OpenAI"

    BASE_URL = "https://api.openai.com/v1"

    AVAILABLE_MODELS = [
        ModelInfo(id="gpt-4o", name="GPT-4o", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="gpt-4-turbo", name="GPT-4 Turbo", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="gpt-3.5-turbo", name="GPT-3.5 Turbo", provider="openai", context_length=16385),
        ModelInfo(id="o1", name="o1", provider="openai", context_length=200000),
        ModelInfo(id="o1-mini", name="o1 Mini", provider="openai", context_length=128000),
        ModelInfo(id="o3-mini", name="o3 Mini", provider="openai", context_length=200000),
    ]

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key)

    async def list_models(self):
        """Return a static list of popular OpenAI models."""
        return list(self.AVAILABLE_MODELS)
