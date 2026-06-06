"""Xiaomi MiMo API provider (via OpenRouter — OpenAI-compatible)."""

import httpx
import json
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class XiaomiProvider(BaseProvider):
    """Xiaomi MiMo API provider via OpenRouter."""

    name = "xiaomi"
    display_name = "Xiaomi (MiMo)"

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_TIMEOUT = 120

    AVAILABLE_MODELS = [
        ModelInfo(id="xiaomi/mimo-7b", name="MiMo 7B", provider="xiaomi", context_length=131072),
        ModelInfo(id="xiaomi/mimo-7b-rl", name="MiMo 7B RL", provider="xiaomi", context_length=131072),
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexuschat.dev",
            "X-Title": "NexusChat",
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
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError("Xiaomi API key not configured. Add an OpenRouter API key in Settings → Providers → Xiaomi.")

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, False),
            )
            if resp.status_code == 401:
                raise ValueError("Invalid OpenRouter API key for Xiaomi provider")
            if resp.status_code == 429:
                raise ValueError("OpenRouter rate limit exceeded")
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
            raise ValueError("Xiaomi API key not configured. Add an OpenRouter API key in Settings → Providers → Xiaomi.")

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, True),
            ) as resp:
                if resp.status_code == 401:
                    raise ValueError("Invalid OpenRouter API key for Xiaomi provider")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

    async def list_models(self):
        """Always return available models — key check happens at chat time."""
        return list(self.AVAILABLE_MODELS)

    async def is_available(self):
        if not self.api_key:
            return False
        return True
