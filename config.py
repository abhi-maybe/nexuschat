"""NexusChat configuration management."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"  # bind to all interfaces
    port: int = 8080
    secret_key: str = "change...n"
    debug: bool = False

    # Database
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'nexuschat.db'}"

    # Provider defaults
    default_provider: str = "ollama"
    default_model: str = "llama3.2"

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Session
    session_lifetime_hours: int = 72

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
