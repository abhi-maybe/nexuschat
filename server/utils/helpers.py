"""Utility functions."""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from jose import jwt
from config import settings
import logging

logger = logging.getLogger(__name__)

# passlib + bcrypt compatibility: bcrypt >= 4.1 broke passlib's auto-truncation.
# We use bcrypt 4.0.1 pinned in requirements.txt, but add a safety net.
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_PASSLIB = True
except Exception:
    logger.warning("passlib/bcrypt unavailable, falling back to hashlib")
    USE_PASSLIB = False

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if USE_PASSLIB:
        return pwd_context.hash(password)
    # Fallback: SHA-256 with salt (not ideal, but functional)
    salt = secrets.token_hex(16)
    return f"sha256${salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    if USE_PASSLIB:
        try:
            return pwd_context.verify(plain, hashed)
        except Exception as e:
            logger.error("Password verification error: %s", e)
            return False
    # Fallback verification
    if hashed.startswith("sha256$"):
        parts = hashed.split("$")
        if len(parts) == 3:
            salt = parts[1]
            expected = hashlib.sha256((salt + plain).encode()).hexdigest()
            return expected == parts[2]
    return False


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
    clean = first_message.strip().replace("\n", " ")
    if len(clean) > 60:
        return clean[:57] + "..."
    return clean if clean else "New Conversation"
