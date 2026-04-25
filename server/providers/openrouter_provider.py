"""OpenRouter API provider — unified access to 200+ models."""

from server.providers.base import ModelInfo
from server.providers.openai_compatible import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter unified API provider."""

    name = "openrouter"
    display_name = "OpenRouter"

    BASE_URL = "https://openrouter.ai/api/v1"

    AVAILABLE_MODELS = [
        ModelInfo(id="openai/gpt-4o", name="GPT-4o", provider="openrouter", context_length=128000),
        ModelInfo(id="openai/gpt-4o-mini", name="GPT-4o Mini", provider="openrouter", context_length=128000),
        ModelInfo(id="anthropic/claude-sonnet-4", name="Claude Sonnet 4", provider="openrouter", context_length=200000),
        ModelInfo(id="anthropic/claude-3.5-haiku", name="Claude 3.5 Haiku", provider="openrouter", context_length=200000),
        ModelInfo(id="google/gemini-2.5-flash", name="Gemini 2.5 Flash", provider="openrouter", context_length=1000000),
        ModelInfo(id="google/gemini-2.5-pro", name="Gemini 2.5 Pro", provider="openrouter", context_length=1000000),
        ModelInfo(id="meta-llama/llama-3.3-70b-instruct", name="Llama 3.3 70B", provider="openrouter", context_length=131072),
        ModelInfo(id="deepseek/deepseek-chat-v3-0324", name="DeepSeek V3", provider="openrouter", context_length=65536),
        ModelInfo(id="deepseek/deepseek-r1", name="DeepSeek R1", provider="openrouter", context_length=65536),
        ModelInfo(id="mistralai/mistral-large-2411", name="Mistral Large", provider="openrouter", context_length=131072),
        ModelInfo(id="qwen/qwen3-235b-a22b", name="Qwen 3 235B", provider="openrouter", context_length=131072),
        ModelInfo(id="x-ai/grok-3-mini", name="Grok 3 Mini", provider="openrouter", context_length=131072),
    ]

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key)

    def _headers(self) -> dict[str, str]:
        """OpenRouter requires HTTP-Referer and X-Title headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexuschat.dev",
            "X-Title": "NexusChat",
        }

    async def list_models(self):
        return list(self.AVAILABLE_MODELS)
