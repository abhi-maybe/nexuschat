"""SQLAlchemy models for NexusChat."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """User account model."""
    """User account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", uselist=False, back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """Per-user settings and API keys."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    openai_api_key = Column(String(256), default="")
    anthropic_api_key = Column(String(256), default="")
    ollama_base_url = Column(String(256), default="http://localhost:11434")
    default_provider = Column(String(32), default="ollama")
    default_model = Column(String(64), default="llama3.2")
    theme = Column(String(16), default="dark")
    system_prompt = Column(Text, default="You are a helpful assistant.")

    user = relationship("User", back_populates="settings")


class Conversation(Base):
    """A chat conversation."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(256), default="New Conversation")
    provider = Column(String(32), default="ollama")
    model = Column(String(64), default="llama3.2")
    system_prompt = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """A single message in a conversation."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model = Column(String(64), default="")
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")
