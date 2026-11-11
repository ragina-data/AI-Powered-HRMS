
"""
Security Utilities
==================

Purpose:
    Centralized security functions for the AI-Powered HRMS application.

Responsibilities:
    1. Secure password hashing and verification using Argon2.
    2. Generate signed JWT access tokens.
    3. Generate signed JWT refresh tokens.
    4. Decode and validate JWT tokens.
    5. Generate SHA-256 hashes of refresh tokens for database storage.

Security Design:
    - Passwords are never stored as plain text.
    - Access tokens have a short expiration period.
    - Refresh tokens have a longer expiration period.
    - Each JWT contains a unique token identifier (jti).
    - Each JWT is associated with a database session (sid).
    - Access and refresh tokens have different token types.
    - Only hashed refresh tokens are stored in PostgreSQL.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import uuid

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


# ============================================================
# 1. PASSWORD HASHING CONFIGURATION
# ============================================================

# Initialize the recommended password hashing configuration.
# pwdlib uses Argon2 as the recommended secure hashing algorithm.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Securely hash a plain-text password using Argon2.

    Args:
        password: Original plain-text password.

    Returns:
        str: Argon2 password hash.

    Note:
        The returned hash should be stored in the users.password_hash
        database column. Never store the original password.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its stored Argon2 hash.

    Args:
        plain_password: Password entered by the user.
        hashed_password: Previously stored Argon2 hash.

    Returns:
        bool: True if the password matches; otherwise False.
    """

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# ============================================================
# 2. ACCESS TOKEN GENERATION
# ============================================================

def create_access_token(
    user_id: int,
    session_id: int,
    expires_delta: timedelta | None = None,
) -> tuple[str, uuid.UUID]:
    """
    Generate a signed JWT access token.

    Access tokens are short-lived credentials used to authenticate
    API requests.

    JWT claims:
        sub: User ID.
        sid: Database session ID.
        jti: Unique identifier for this access token.
        typ: Token type (access).
        iat: Token issued-at timestamp.
        exp: Token expiration timestamp.

    Args:
        user_id: Authenticated user's database ID.
        session_id: Associated user_sessions record ID.
        expires_delta: Optional custom expiration duration.

    Returns:
        tuple:
            - Encoded JWT access token.
            - UUID used as the token's unique identifier.

    Note:
        The access-token JTI is stored in user_sessions so that
        the API can validate the token against the active session.
    """

    now = datetime.now(timezone.utc)

    # Use the configured access-token expiration when no
    # custom expiration duration is provided.
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = now + expires_delta

    # Generate a unique identifier for this access token.
    token_jti = uuid.uuid4()

    # Define the JWT payload.
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(token_jti),
        "typ": "access",
        "iat": now,
        "exp": expire,
    }

    # Sign the JWT using the application's secret key.
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return token, token_jti


# ============================================================
# 3. REFRESH TOKEN GENERATION
# ============================================================

def create_refresh_token(
    user_id: int,
    session_id: int,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Generate a signed JWT refresh token.

    Refresh tokens are used to obtain new access tokens after
    the existing access token expires.

    JWT claims:
        sub: User ID.
        sid: Associated database session ID.
        jti: Unique identifier for this refresh token.
        typ: Token type (refresh).
        iat: Token issued-at timestamp.
        exp: Token expiration timestamp.

    Args:
        user_id: Authenticated user's database ID.
        session_id: Associated user_sessions record ID.
        expires_delta: Optional custom expiration duration.

    Returns:
        tuple:
            - Encoded JWT refresh token.
            - Refresh-token expiration timestamp.

    Security:
        The raw refresh token must never be stored in the database.
        Store its SHA-256 hash instead.
    """

    now = datetime.now(timezone.utc)

    # Use the configured refresh-token expiration.
    if expires_delta is None:
        expires_delta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    expire = now + expires_delta

    # Generate a unique identifier for this refresh token.
    token_jti = uuid.uuid4()

    # Define the JWT payload.
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(token_jti),
        "typ": "refresh",
        "iat": now,
        "exp": expire,
    }

    # Sign the refresh token.
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return token, expire


# ============================================================
# 4. GENERIC JWT DECODING AND VALIDATION
# ============================================================

def decode_token(token: str) -> dict | None:
    """
    Decode and validate a signed JWT.

    Validates:
        - JWT signature.
        - Signing algorithm.
        - Token expiration.

    Args:
        token: Encoded JWT string.

    Returns:
        dict: Decoded JWT payload if valid.
        None: If the token is invalid or expired.

    Note:
        This function validates the JWT cryptographically.
        Database session validation is performed separately
        by the authentication dependencies.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        return payload

    except InvalidTokenError:
        # Invalid signatures, expired tokens and malformed
        # JWTs are rejected.
        return None


# ============================================================
# 5. ACCESS TOKEN VALIDATION
# ============================================================

def decode_access_token(token: str) -> dict | None:
    """
    Decode a JWT and ensure that it is an access token.

    Prevents a refresh token from being used as an access token.

    Args:
        token: Encoded JWT string.

    Returns:
        dict: Valid access-token payload.
        None: If invalid or if the token type is incorrect.
    """

    payload = decode_token(token)

    # Reject invalid tokens and tokens of another type.
    if payload is None or payload.get("typ") != "access":
        return None

    return payload


# ============================================================
# 6. REFRESH TOKEN VALIDATION
# ============================================================

def decode_refresh_token(token: str) -> dict | None:
    """
    Decode a JWT and ensure that it is a refresh token.

    Prevents an access token from being used to refresh
    authentication credentials.

    Args:
        token: Encoded JWT string.

    Returns:
        dict: Valid refresh-token payload.
        None: If invalid or if the token type is incorrect.
    """

    payload = decode_token(token)

    # Reject invalid tokens and tokens of another type.
    if payload is None or payload.get("typ") != "refresh":
        return None

    return payload


# ============================================================
# 7. REFRESH TOKEN HASHING
# ============================================================

def hash_refresh_token(token: str) -> str:
    """
    Generate a SHA-256 hash of a refresh token.

    Purpose:
        Store a one-way hash of the refresh token in PostgreSQL
        instead of storing the original token.

    Args:
        token: Original encoded refresh token.

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 hash.

    Database:
        Stored in user_sessions.refresh_token_hash.

    Note:
        SHA-256 is appropriate here because refresh tokens are
        cryptographically random, high-entropy credentials.
        Passwords must continue to use Argon2 instead.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
