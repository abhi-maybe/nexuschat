"""Model listing and provider status routes."""

from fastapi import APIRouter, Request, Depends
from server.routes.auth import get_current_user, get_db
from server.database.models import User, UserSettings
import logging

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/available")
async def list_available_models(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List all models from all configured providers."""
    registry = request.app.state.providers

    # Load user settings and configure providers
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if settings:
        registry.configure_provider("ollama", base_url=settings.ollama_base_url)
        registry.configure_provider("openai", api_key=settings.openai_api_key)
        registry.configure_provider("anthropic", api_key=settings.anthropic_api_key)

    models = await registry.get_available_models()
    logger.info("Listed %d models for user %d", len(models), user.id)
    return {"models": models}


@router.get("/status")
async def provider_status(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check which providers are available."""
    registry = request.app.state.providers

    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if settings:
        registry.configure_provider("ollama", base_url=settings.ollama_base_url)
        registry.configure_provider("openai", api_key=settings.openai_api_key)
        registry.configure_provider("anthropic", api_key=settings.anthropic_api_key)

    status = await registry.get_status()
    return {"providers": status}
