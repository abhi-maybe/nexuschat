"""Xiaomi MiMo API provider (OpenAI-compatible, custom auth header)."""

from server.providers.base import ModelInfo
from server.providers.openai_compatible import OpenAICompatibleProvider


class XiaomiProvider(OpenAICompatibleProvider):
    """Xiaomi MiMo API provider."""

    name = "xiaomi"
    display_name = "Xiaomi (MiMo)"

    BASE_URL = "https://api.xiaomimimo.com/v1"

    AVAILABLE_MODELS = [
        ModelInfo(id="mimo-v2.5-pro", name="MiMo V2.5 Pro (Flagship)", provider="xiaomi", context_length=1048576),
        ModelInfo(id="mimo-v2.5", name="MiMo V2.5 (Omnimodal)", provider="xiaomi", context_length=1048576),
        ModelInfo(id="mimo-v2-flash", name="MiMo V2 Flash (Fast)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-flash-thinking", name="MiMo V2 Flash Thinking (Reasoning)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-omni", name="MiMo V2 Omni (Multimodal)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-pro", name="MiMo V2 Pro (Agent)", provider="xiaomi", context_length=262144),
    ]

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key)

    def _headers(self) -> dict[str, str]:
        """Xiaomi uses ``api-key`` header instead of ``Authorization: Bearer``."""
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages, model, system_prompt, temperature, max_tokens, stream=False):
        """Use ``max_completion_tokens`` and ``top_p`` for Xiaomi."""
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            msgs.append({"role": m.role, "content": m.content})
        return {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "top_p": 0.95,
            "stream": stream,
        }

    async def list_models(self):
        return list(self.AVAILABLE_MODELS)
