"""Authentication routes."""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import User, UserSettings
from server.utils.helpers import hash_password, verify_password, create_token, decode_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


async def get_db(request: Request):
    async with request.app.state.db.get_session() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Extract user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(auth[7:])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        logger.warning("Failed login attempt for user: %s", req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info("User logged in: %s", user.username)
    token = create_token({"sub": str(user.id), "username": user.username})
    return {"token": token, "username": user.username, "user_id": user.id}


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    result = await db.execute(select(User).where(User.username == req.username.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    if len(req.username) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    user = User(username=req.username, password_hash=hash_password(req.password))
    db.add(user)
    await db.flush()

    # Create default settings
    settings = UserSettings(user_id=user.id)
    db.add(settings)
    await db.commit()
    await db.refresh(user)

    token = create_token({"sub": str(user.id), "username": user.username})
    return {"token": token, "username": user.username, "user_id": user.id}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"user_id": user.id, "username": user.username}
