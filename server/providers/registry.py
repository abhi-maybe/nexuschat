"""Provider registry - discovers and manages AI providers."""

from server.providers.base import BaseProvider
from server.providers.ollama_provider import OllamaProvider
from server.providers.openai_provider import OpenAIProvider
from server.providers.anthropic_provider import AnthropicProvider
from server.providers.deepseek_provider import DeepSeekProvider
from server.providers.xiaomi_provider import XiaomiProvider
from server.providers.groq_provider import GroqProvider
from server.providers.openrouter_provider import OpenRouterProvider


class ProviderRegistry:
    """Central registry for all AI providers."""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def discover_providers(self):
        """Register all known providers."""
        self._providers["ollama"] = OllamaProvider()
        self._providers["openai"] = OpenAIProvider()
        self._providers["anthropic"] = AnthropicProvider()
        self._providers["deepseek"] = DeepSeekProvider()
        self._providers["xiaomi"] = XiaomiProvider()
        self._providers["groq"] = GroqProvider()
        self._providers["openrouter"] = OpenRouterProvider()

    def get_provider(self, name: str) -> BaseProvider | None:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_all_providers(self) -> dict[str, BaseProvider]:
        return dict(self._providers)

    def configure_provider(self, name: str, **kwargs):
        """Update provider configuration (API keys, URLs).

        Creates a new provider instance with updated config instead of
        mutating the shared singleton, avoiding race conditions.
        """
        provider = self._providers.get(name)
        if not provider:
            return

        if name == "ollama" and "base_url" in kwargs:
            new_url = kwargs["base_url"].rstrip("/")
            if new_url != provider.base_url:
                new_provider = OllamaProvider(base_url=new_url)
                self._providers[name] = new_provider
        elif name in ("openai", "anthropic", "deepseek", "xiaomi", "groq", "openrouter") and "api_key" in kwargs:
            new_key = kwargs["api_key"]
            if new_key != provider.api_key:
                provider_class = type(provider)
                new_provider = provider_class(api_key=new_key)
                self._providers[name] = new_provider

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
