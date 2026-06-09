"""User settings routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from server.routes.auth import get_current_user, get_db
from server.database.models import User, UserSettings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    xiaomi_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    theme: Optional[str] = None
    system_prompt: Optional[str] = None


@router.get("/")
async def get_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "openai_api_key": bool(settings.openai_api_key),
        "anthropic_api_key": bool(settings.anthropic_api_key),
        "deepseek_api_key": bool(settings.deepseek_api_key),
        "xiaomi_api_key": bool(settings.xiaomi_api_key),
        "groq_api_key": bool(settings.groq_api_key),
        "openrouter_api_key": bool(settings.openrouter_api_key),
        "ollama_base_url": settings.ollama_base_url,
        "default_provider": settings.default_provider,
        "default_model": settings.default_model,
        "theme": settings.theme,
        "system_prompt": settings.system_prompt,
    }


@router.put("/")
async def update_settings(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    updates = body.model_dump(exclude_none=True)
    logger.info("Settings updated for user %d: %s", user.id, list(updates.keys()))
    allowed_fields = {
        'openai_api_key', 'anthropic_api_key', 'deepseek_api_key',
        'xiaomi_api_key', 'groq_api_key', 'openrouter_api_key', 'ollama_base_url',
        'default_provider', 'default_model', 'theme', 'system_prompt'
    }
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(settings, field, value)

    await db.commit()
    return {"status": "updated"}
