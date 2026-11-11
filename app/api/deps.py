
"""
Authentication Dependencies
============================

Purpose:
    Validate OAuth2 Bearer access tokens and retrieve the
    authenticated user and corresponding database session.

Security checks:
    1. Validate JWT signature and access-token type.
    2. Validate required JWT claims.
    3. Verify that the user account is active.
    4. Verify that the database session exists.
    5. Verify that the session belongs to the authenticated user.
    6. Verify that the session has not expired or been revoked.
    7. Verify that the access-token JTI matches the stored session JTI.

Design:
    get_current_user_and_session()
        Returns both the authenticated user and its exact session.

    get_current_user()
        Returns only the authenticated user.

    This preserves compatibility with existing API endpoints
    while allowing session-specific operations such as logout.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.user_session import UserSession


# ============================================================
# OAUTH2 BEARER AUTHENTICATION
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="OAuth2PasswordBearer",
)


# ============================================================
# CURRENT USER AND SESSION DEPENDENCY
# ============================================================

def get_current_user_and_session(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> tuple[User, UserSession]:
    """
    Validate the supplied JWT access token.

    Return:
        A tuple containing:
            1. Authenticated User.
            2. Matching active UserSession.

    The returned session allows individual device sessions
    to be managed independently.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --------------------------------------------------------
    # STEP 1: Decode and validate the access token.
    # --------------------------------------------------------

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # --------------------------------------------------------
    # STEP 2: Extract the required JWT claims.
    # --------------------------------------------------------

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    token_jti = payload.get("jti")

    if not user_id or not session_id or not token_jti:
        raise credentials_exception

    # --------------------------------------------------------
    # STEP 3: Validate claim formats.
    # --------------------------------------------------------

    try:
        user_id = int(user_id)
        session_id = int(session_id)
        token_jti = UUID(str(token_jti))

    except (TypeError, ValueError, AttributeError):
        raise credentials_exception

    if user_id <= 0 or session_id <= 0:
        raise credentials_exception

    # --------------------------------------------------------
    # STEP 4: Retrieve the active user.
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if user is None:
        raise credentials_exception

    # --------------------------------------------------------
    # STEP 5: Retrieve the matching active database session.
    # --------------------------------------------------------

    user_session = (
        db.query(UserSession)
        .filter(
            UserSession.session_id == session_id,
            UserSession.user_id == user_id,
            UserSession.access_token_jti == token_jti,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if user_session is None:
        raise credentials_exception

    # --------------------------------------------------------
    # STEP 6: Return both authenticated objects.
    # --------------------------------------------------------

    return user, user_session


# ============================================================
# CURRENT USER DEPENDENCY
# ============================================================

def get_current_user(
    authentication: Annotated[
        tuple[User, UserSession],
        Depends(get_current_user_and_session),
    ],
) -> User:
    """
    Return only the authenticated user.

    Existing endpoints can continue using this dependency
    without requiring any changes.
    """

    user, _ = authentication

    return user
