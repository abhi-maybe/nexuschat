"""DeepSeek API provider (OpenAI-compatible)."""

from server.providers.base import ModelInfo
from server.providers.openai_compatible import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek API provider."""

    name = "deepseek"
    display_name = "DeepSeek"

    BASE_URL = "https://api.deepseek.com/v1"

    AVAILABLE_MODELS = [
        ModelInfo(id="deepseek-chat", name="DeepSeek Chat", provider="deepseek", context_length=65536),
        ModelInfo(id="deepseek-coder", name="DeepSeek Coder", provider="deepseek", context_length=65536),
        ModelInfo(id="deepseek-reasoner", name="DeepSeek Reasoner", provider="deepseek", context_length=65536),
    ]

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key)

    async def list_models(self):
        return list(self.AVAILABLE_MODELS)
