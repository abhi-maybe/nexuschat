"""Ollama local model provider."""

import httpx
from typing import AsyncGenerator
from server.providers.base import BaseProvider, ChatMessage, ChatResponse, ModelInfo


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
                import json
                async for line in resp.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]

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
                        context_length=m.get("details", {}).get("parameter_size", "unknown") if isinstance(m.get("details"), dict) else 4096,
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
                import json
                async for line in resp.aiter_lines():
                    if line.strip():
                        yield json.loads(line)
