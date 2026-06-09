"""Ollama local model provider."""

import httpx
import json
import logging
from typing import AsyncGenerator

from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama local inference provider."""

    name = "ollama"
    display_name = "Ollama (Local)"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def chat(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            msgs.append({"role": m.role, "content": m.content})

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": msgs,
                        "stream": False,
                        "options": {"temperature": temperature, "num_predict": max_tokens},
                    },
                )
                resp.raise_for_status()
        except httpx.ConnectError:
            raise ValueError("Cannot connect to Ollama. Is it running?")
        except httpx.TimeoutException:
            raise ValueError("Ollama request timed out")

        data = resp.json()
        return ChatResponse(
            content=data["message"]["content"],
            model=model,
            tokens_used=data.get("eval_count", 0),
            provider=self.name,
        )

    async def chat_stream(self, messages, model, system_prompt="", temperature=0.7, max_tokens=4096):
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            msgs.append({"role": m.role, "content": m.content})

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": msgs,
                        "stream": True,
                        "options": {"temperature": temperature, "num_predict": max_tokens},
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
        except httpx.ConnectError:
            raise ValueError("Cannot connect to Ollama. Is it running?")
        except httpx.ReadTimeout:
            raise ValueError("Ollama request timed out")

    @staticmethod
    def _parse_parameter_size(param_size) -> int:
        """Convert Ollama parameter_size (e.g. '7B', '13B') to an int context_length."""
        if isinstance(param_size, int):
            return param_size
        if isinstance(param_size, str):
            import re
            match = re.search(r"(\d+(?:\.\d+)?)\s*([BMK])?", param_size.upper())
            if match:
                value = float(match.group(1))
                unit = match.group(2) or ""
                multiplier = {"B": 1_000_000_000, "M": 1_000_000, "K": 1_000, "": 1}.get(unit, 1)
                return int(value * multiplier)
        return 4096

    async def list_models(self):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [
                    ModelInfo(
                        id=m["name"],
                        name=m["name"],
                        provider=self.name,
                        context_length=self._parse_parameter_size(
                            m.get("details", {}).get("parameter_size", 4096)
                            if isinstance(m.get("details"), dict) else 4096
                        ),
                    )
                    for m in data.get("models", [])
                ]
        except Exception as e:
            logger.debug("Ollama unavailable: %s", e)
            return []

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def pull_model(self, model_name: str) -> AsyncGenerator[dict, None]:
        """Pull/download a model."""
        async with httpx.AsyncClient(timeout=3600) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield json.loads(line)
