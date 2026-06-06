"""Xiaomi MiMo API provider (OpenAI-compatible)."""

import httpx
import json
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class XiaomiProvider(BaseProvider):
    """Xiaomi MiMo API provider."""

    name = "xiaomi"
    display_name = "Xiaomi (MiMo)"

    BASE_URL = "https://api.xiaomimimo.com/v1"
    DEFAULT_TIMEOUT = 120

    AVAILABLE_MODELS = [
        ModelInfo(id="mimo-v2.5-pro", name="MiMo V2.5 Pro (Flagship)", provider="xiaomi", context_length=1048576),
        ModelInfo(id="mimo-v2.5", name="MiMo V2.5 (Omnimodal)", provider="xiaomi", context_length=1048576),
        ModelInfo(id="mimo-v2-flash", name="MiMo V2 Flash (Fast)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-flash-thinking", name="MiMo V2 Flash Thinking (Reasoning)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-omni", name="MiMo V2 Omni (Multimodal)", provider="xiaomi", context_length=262144),
        ModelInfo(id="mimo-v2-pro", name="MiMo V2 Pro (Agent)", provider="xiaomi", context_length=262144),
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _headers(self):
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages, model, system_prompt, temperature, max_tokens, stream=False):
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

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError("Xiaomi API key not configured. Add one in Settings → Providers → Xiaomi.")

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, False),
            )
            if resp.status_code == 401:
                raise ValueError("Invalid Xiaomi API key")
            if resp.status_code == 429:
                raise ValueError("Xiaomi rate limit exceeded")
            resp.raise_for_status()

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return ChatResponse(
            content=choice["message"]["content"],
            model=model,
            tokens_used=usage.get("total_tokens", 0),
            provider=self.name,
        )

    async def chat_stream(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError("Xiaomi API key not configured. Add one in Settings → Providers → Xiaomi.")

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, True),
            ) as resp:
                if resp.status_code == 401:
                    raise ValueError("Invalid Xiaomi API key")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

    async def list_models(self):
        return list(self.AVAILABLE_MODELS)

    async def is_available(self):
        if not self.api_key:
            return False
        return True
