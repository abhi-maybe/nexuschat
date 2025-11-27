"""Utility functions."""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from jose import jwt
from passlib.context import CryptContext
from config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict, expires_hours: int = 168) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def generate_title(first_message: str) -> str:
    """Generate a short title from the first message."""
    """Generate a conversation title from the first message."""
    clean = first_message.strip().replace("\n", " ")
    if len(clean) > 60:
        return clean[:57] + "..."
    return clean if clean else "New Conversation"
