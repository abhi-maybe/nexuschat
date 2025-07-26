"""Provider registry - discovers and manages AI providers."""

from server.providers.base import BaseProvider
from server.providers.ollama_provider import OllamaProvider
from server.providers.openai_provider import OpenAIProvider
from server.providers.anthropic_provider import AnthropicProvider


class ProviderRegistry:
    """Central registry for all AI providers."""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def discover_providers(self):
        """Register all known providers."""
        self._providers["ollama"] = OllamaProvider()
        self._providers["openai"] = OpenAIProvider()
        self._providers["anthropic"] = AnthropicProvider()

    def get_provider(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def get_all_providers(self) -> dict[str, BaseProvider]:
        return self._providers

    def configure_provider(self, name: str, **kwargs):
        """Update provider configuration (API keys, URLs)."""
        provider = self._providers.get(name)
        if not provider:
            return

        if name == "ollama" and "base_url" in kwargs:
            provider.base_url = kwargs["base_url"].rstrip("/")
        elif name == "openai" and "api_key" in kwargs:
            provider.api_key = kwargs["api_key"]
        elif name == "anthropic" and "api_key" in kwargs:
            provider.api_key = kwargs["api_key"]

    async def get_available_models(self) -> list[dict]:
        """Get models from all available providers."""
        all_models = []
        for name, provider in self._providers.items():
            try:
                models = await provider.list_models()
                for m in models:
                    all_models.append({
                        "id": m.id,
                        "name": m.name,
                        "provider": m.provider,
                        "provider_display": provider.display_name,
                        "context_length": m.context_length,
                        "supports_vision": m.supports_vision,
                    })
            except Exception:
                continue
        return all_models

    async def get_status(self) -> dict[str, bool]:
        """Check availability of all providers."""
        status = {}
        for name, provider in self._providers.items():
            try:
                status[name] = await provider.is_available()
            except Exception:
                status[name] = False
        return status
