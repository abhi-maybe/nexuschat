"""OpenRouter API provider — unified access to 200+ models."""

import httpx
import json
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class OpenRouterProvider(BaseProvider):
    """OpenRouter unified API provider."""

    name = "openrouter"
    display_name = "OpenRouter"

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_TIMEOUT = 120

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
            raise ValueError("OpenRouter API key not configured. Add one in Settings → Providers → OpenRouter.")

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, False),
            )
            if resp.status_code == 401:
                raise ValueError("Invalid OpenRouter API key")
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
            raise ValueError("OpenRouter API key not configured. Add one in Settings → Providers → OpenRouter.")

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, True),
            ) as resp:
                if resp.status_code == 401:
                    raise ValueError("Invalid OpenRouter API key")
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
