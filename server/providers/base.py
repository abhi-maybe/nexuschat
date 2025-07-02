"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    tokens_used: int = 0
    provider: str = ""


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    context_length: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False


class BaseProvider(ABC):
    """Base class all providers must implement."""

    name: str = "base"
    display_name: str = "Base Provider"

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion response."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models from this provider."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is reachable and configured."""
        ...
