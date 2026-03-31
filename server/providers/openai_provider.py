"""OpenAI API provider."""

import httpx
from typing import AsyncGenerator
from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""
    name = "openai"
    display_name = "OpenAI"

    BASE_URL = "https://api.openai.com/v1"
    DEFAULT_TIMEOUT = 120

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
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json=self._build_payload(messages, model, system_prompt, temperature, max_tokens, False),
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid OpenAI API key")
            if e.response.status_code == 429:
                raise ValueError("OpenAI rate limit exceeded")
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
                        import json
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

    async def list_models(self):
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.BASE_URL}/models", headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("data", []):
                    if "gpt" in m["id"] or "o1" in m["id"] or "o3" in m["id"]:
                        models.append(ModelInfo(
                            id=m["id"],
                            name=m["id"],
                            provider=self.name,
                        ))
                return sorted(models, key=lambda x: x.id)
        except Exception:
            return []

    async def is_available(self):
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.BASE_URL}/models", headers=self._headers())
                return resp.status_code == 200
        except Exception:
            return False
