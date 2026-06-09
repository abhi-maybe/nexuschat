"""Chat and conversation routes."""

import json
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional

from server.routes.auth import get_current_user
from server.routes.auth import get_db
from server.database.models import User, UserSettings, Conversation, Message
from server.providers.base import ChatMessage
from server.utils.helpers import generate_title
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    model: str = "llama3.2"
    provider: str = "ollama"
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True
    parent_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None


async def _get_or_create_conversation(db, user_id, conv_id, provider, model, system_prompt):
    if conv_id:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conv_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = Conversation(
        user_id=user_id,
        title="New Conversation",
        provider=provider,
        model=model,
        system_prompt=system_prompt,
    )
    db.add(conv)
    await db.flush()
    return conv


async def _load_history(db, conversation_id, limit=50):
    from sqlalchemy import asc
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(asc(Message.created_at))
        .limit(limit)
    )
    messages = result.scalars().all()
    return [ChatMessage(role=m.role, content=m.content) for m in messages]


@router.post("/send")
async def send_message(
    req: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response (streaming or complete)."""
    registry = request.app.state.providers

    # Load user settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if settings:
        registry.configure_provider("ollama", base_url=settings.ollama_base_url)
        registry.configure_provider("openai", api_key=settings.openai_api_key)
        registry.configure_provider("anthropic", api_key=settings.anthropic_api_key)
        registry.configure_provider("deepseek", api_key=settings.deepseek_api_key)
        registry.configure_provider("xiaomi", api_key=settings.xiaomi_api_key)
        registry.configure_provider("groq", api_key=settings.groq_api_key)
        registry.configure_provider("openrouter", api_key=settings.openrouter_api_key)

    provider = registry.get_provider(req.provider)
    if not provider:
        logger.error("Unknown provider requested: %s", req.provider)
        raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")

    # Get/create conversation
    conv = await _get_or_create_conversation(db, user.id, req.conversation_id, req.provider, req.model, req.system_prompt)
    logger.info("Chat request: provider=%s model=%s conv=%s", req.provider, req.model, conv.id)

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=req.message, model=req.model, parent_id=req.parent_id)
    db.add(user_msg)

    # Update title if first message
    is_new = not req.conversation_id
    if is_new:
        conv.title = generate_title(req.message)
    else:
        msg_count = len(conv.messages) if conv.messages else 0
        if msg_count == 0:
            conv.title = generate_title(req.message)

    # Flush so user message is visible to subsequent queries
    await db.flush()

    # Load conversation history (now includes the just-added user message)
    history = await _load_history(db, conv.id)

    # Get system prompt
    system = req.system_prompt or conv.system_prompt or (settings.system_prompt if settings else "")

    await db.commit()

    if req.stream:
        async def stream_response():
            full_content = ""
            try:
                async for chunk in provider.chat_stream(
                    history, req.model, system, req.temperature, req.max_tokens
                ):
                    full_content += chunk
                    payload = json.dumps({"content": chunk, "conversation_id": conv.id})
                    yield f"data: {payload}\n\n"
            except httpx.ConnectError:
                logger.error("Connection error: provider=%s model=%s", req.provider, req.model)
                err_payload = json.dumps({"error": f"Cannot connect to {req.provider} API"})
                yield f"data: {err_payload}\n\n"
                return
            except httpx.ReadTimeout:
                logger.error("Read timeout: provider=%s model=%s", req.provider, req.model)
                err_payload = json.dumps({"error": f"{req.provider} API timed out"})
                yield f"data: {err_payload}\n\n"
                return
            except httpx.HTTPStatusError as e:
                logger.error("HTTP error: provider=%s model=%s status=%s", req.provider, req.model, e.response.status_code)
                err_payload = json.dumps({"error": f"{req.provider} API error (HTTP {e.response.status_code})"})
                yield f"data: {err_payload}\n\n"
                return
            except ValueError as e:
                logger.warning("Stream config error: provider=%s model=%s error=%s", req.provider, req.model, e)
                err_payload = json.dumps({"error": str(e)})
                yield f"data: {err_payload}\n\n"
                return
            except Exception as e:
                logger.error("Stream error: provider=%s model=%s error=%s", req.provider, req.model, e)
                err_payload = json.dumps({"error": str(e)})
                yield f"data: {err_payload}\n\n"
                return

            # Save assistant message
            async with request.app.state.db.get_session() as save_db:
                asst_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_content,
                    model=req.model,
                )
                save_db.add(asst_msg)
                await save_db.commit()

            done_payload = json.dumps({"done": True, "conversation_id": conv.id})
            yield f"data: {done_payload}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        try:
            response = await provider.chat(history, req.model, system, req.temperature, req.max_tokens)
            asst_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=response.content,
                model=req.model,
                tokens_used=response.tokens_used,
            )
            db.add(asst_msg)
            await db.commit()

            return {
                "content": response.content,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "conversation_id": conv.id,
            }
        except ValueError as e:
            logger.warning("Chat config error: provider=%s model=%s error=%s", req.provider, req.model, e)
            raise HTTPException(status_code=400, detail=str(e))
        except httpx.ConnectError:
            logger.error("Connection error: provider=%s model=%s", req.provider, req.model)
            raise HTTPException(status_code=502, detail=f"Cannot connect to {req.provider} API")
        except httpx.ReadTimeout:
            logger.error("Read timeout: provider=%s model=%s", req.provider, req.model)
            raise HTTPException(status_code=504, detail=f"{req.provider} API timed out")
        except Exception as e:
            logger.error("Chat error: provider=%s model=%s error=%s", req.provider, req.model, e)
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
    )
    conversations = result.scalars().unique().all()
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "provider": c.provider,
                "model": c.model,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "message_count": len(c.messages) if c.messages else 0,
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a full conversation with all messages."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "title": conv.title,
        "provider": conv.provider,
        "model": conv.model,
        "system_prompt": conv.system_prompt or "",
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "parent_id": m.parent_id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in conv.messages
        ],
    }


@router.put("/conversations/{conv_id}")
async def update_conversation(
    conv_id: int,
    body: ConversationUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.title is not None:
        conv.title = body.title
    if body.system_prompt is not None:
        conv.system_prompt = body.system_prompt

    await db.commit()
    return {"status": "ok"}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    logger.info("Conversation %d deleted by user %d", conv_id, user.id)
    return {"status": "deleted"}
