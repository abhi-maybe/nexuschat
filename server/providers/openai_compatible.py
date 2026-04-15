"""Shared base class for OpenAI-compatible API providers."""

import json
import logging
from typing import AsyncGenerator

import httpx

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """Base provider for any API that follows the OpenAI chat completions format.

    Subclasses only need to set class-level constants (name, display_name,
    BASE_URL, AVAILABLE_MODELS) and optionally override ``_headers`` for
    non-standard authentication schemes.
    """

    # ---- subclass config ------------------------------------------------
    name: str = "openai_compatible"
    display_name: str = "OpenAI Compatible"

    BASE_URL: str = ""
    DEFAULT_TIMEOUT: int = 120
    AVAILABLE_MODELS: list[ModelInfo] = []

    # ---- constructor ----------------------------------------------------

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    # ---- overridable helpers --------------------------------------------

    def _headers(self) -> dict[str, str]:
        """Return HTTP headers.  Override for non-Bearer auth (e.g. Xiaomi)."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: list[ChatMessage],
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict:
        """Build the JSON body for ``/chat/completions``."""
        msgs: list[dict] = []
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

    # ---- error helpers --------------------------------------------------

    @staticmethod
    def _raise_for_status(resp: httpx.Response, provider_name: str) -> None:
        """Translate common HTTP errors into user-friendly ValueErrors."""
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

    # ---- core API methods -----------------------------------------------

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        if not self.api_key:
            raise ValueError(
                f"{self.display_name} API key not configured. "
                f"Add one in Settings \u2192 Providers \u2192 {self.display_name}."
            )

        payload = self._build_payload(
            messages, model, system_prompt, temperature, max_tokens, stream=False
        )

        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                self._raise_for_status(resp, self.display_name)
        except httpx.ConnectError:
            raise ValueError(f"Cannot connect to {self.display_name} API")
        except httpx.ReadTimeout:
            raise ValueError(f"{self.display_name} API request timed out")

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return ChatResponse(
            content=choice["message"]["content"],
            model=model,
            tokens_used=usage.get("total_tokens", 0),
            provider=self.name,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError(
                f"{self.display_name} API key not configured. "
                f"Add one in Settings \u2192 Providers \u2192 {self.display_name}."
            )

        payload = self._build_payload(
            messages, model, system_prompt, temperature, max_tokens, stream=True
        )

        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    self._raise_for_status(resp, self.display_name)
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except httpx.ConnectError:
            raise ValueError(f"Cannot connect to {self.display_name} API")
        except httpx.ReadTimeout:
            raise ValueError(f"{self.display_name} API request timed out")

    async def list_models(self) -> list[ModelInfo]:
        return list(self.AVAILABLE_MODELS)

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        return True
