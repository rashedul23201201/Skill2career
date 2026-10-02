import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import bcrypt
import jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a salt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Compute a SHA-256 hash of a raw token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str | int,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed JWT access token for authentication."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if claims:
        payload.update(claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str | int,
    remember_me: bool = False
) -> Tuple[str, str, datetime]:
    """Generate a cryptographically random refresh token, its SHA-256 hash, and expiration timestamp."""
    days = settings.REFRESH_TOKEN_EXPIRE_REMEMBER_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    
    # Generate 64 bytes of URL-safe random entropy
    raw_token = secrets.token_urlsafe(64)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash, expires_at


def generate_time_sensitive_token(expires_in_hours: int = 1) -> Tuple[str, str, datetime]:
    """Generate a secure one-time URL-safe token (for password reset or email verification)."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash, expires_at


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
