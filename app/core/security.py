from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


# Password hashing using Argon2
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a password against its stored hash."""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token."""

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        return payload

    except InvalidTokenError:
        return None