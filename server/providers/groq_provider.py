"""Groq API provider (OpenAI-compatible)."""

import httpx
import json
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class GroqProvider(BaseProvider):
    """Groq API provider."""

    name = "groq"
    display_name = "Groq"

    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_TIMEOUT = 120

    AVAILABLE_MODELS = [
        ModelInfo(id="llama-3.3-70b-versatile", name="Llama 3.3 70B", provider="groq", context_length=131072),
        ModelInfo(id="mixtral-8x7b-32768", name="Mixtral 8x7B", provider="groq", context_length=32768),
        ModelInfo(id="gemma2-9b-it", name="Gemma 2 9B", provider="groq", context_length=8192),
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
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
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError("Groq API key not configured. Add one in Settings → Providers → Groq.")
        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers(),
                    json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, False),
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Groq API key")
            if e.response.status_code == 429:
                raise ValueError("Groq rate limit exceeded")
            raise

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
            raise ValueError("Groq API key not configured. Add one in Settings → Providers → Groq.")
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, True),
            ) as resp:
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
