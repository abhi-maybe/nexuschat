"""User settings routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.routes.auth import get_current_user, get_db
from server.database.models import User, UserSettings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SettingsUpdate(BaseModel):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str | None = None
    default_provider: str | None = None
    default_model: str | None = None
    theme: str | None = None
    system_prompt: str | None = None


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
    for field, value in updates.items():
        setattr(settings, field, value)

    await db.commit()
    return {"status": "updated"}
