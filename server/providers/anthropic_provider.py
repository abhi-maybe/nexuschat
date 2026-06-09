"""Anthropic Claude API provider."""

import httpx
import json
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

    name = "anthropic"
    display_name = "Anthropic (Claude)"

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_for_status(resp: httpx.Response, provider_name: str) -> None:
        code = resp.status_code
        if code == 401:
            raise ValueError(f"Invalid {provider_name} API key")
        if code == 429:
            raise ValueError(f"{provider_name} rate limit exceeded")
        if code == 400:
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                detail = resp.text
            raise ValueError(f"{provider_name} request error: {detail}")
        if code >= 500:
            raise ValueError(f"{provider_name} server error (HTTP {code})")
        resp.raise_for_status()

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Add one in Settings \u2192 Providers \u2192 Anthropic (Claude)."
            )

        msgs = [{"role": m.role, "content": m.content} for m in messages]
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msgs,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/messages",
                    headers=self._headers(),
                    json=payload,
                )
                self._raise_for_status(resp, self.display_name)
        except httpx.ConnectError:
            raise ValueError("Cannot connect to Anthropic API")
        except httpx.ReadTimeout:
            raise ValueError("Anthropic API request timed out")

        data = resp.json()
        return ChatResponse(
            content=data["content"][0]["text"],
            model=model,
            tokens_used=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
            provider=self.name,
        )

    async def chat_stream(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Add one in Settings \u2192 Providers \u2192 Anthropic (Claude)."
            )

        msgs = [{"role": m.role, "content": m.content} for m in messages]
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msgs,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/messages",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    self._raise_for_status(resp, self.display_name)
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            chunk = json.loads(line[6:])
                            if chunk.get("type") == "content_block_delta":
                                yield chunk["delta"].get("text", "")
        except httpx.ConnectError:
            raise ValueError("Cannot connect to Anthropic API")
        except httpx.ReadTimeout:
            raise ValueError("Anthropic API request timed out")

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="claude-sonnet-4-20250514", name="Claude Sonnet 4", provider=self.name, context_length=200000, supports_vision=True),
            ModelInfo(id="claude-3-5-haiku-20241022", name="Claude 3.5 Haiku", provider=self.name, context_length=200000, supports_vision=True),
        ]

    async def is_available(self):
        if not self.api_key:
            return False
        return True
