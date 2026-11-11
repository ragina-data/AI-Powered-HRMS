
"""
Authentication API
==================

Purpose:
    Provide secure authentication and user identity endpoints.

Endpoints:
    POST /login
        Authenticate a user and create a database-backed session.

    GET /me
        Return the currently authenticated user's profile.

Additional endpoints will be added incrementally:
    POST /refresh
    POST /logout
    POST /change-password
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from argon2 import hash_password
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy import update
from app.api.deps import (
    get_current_user,
    get_current_user_and_session,
)

from app.core.config import settings
from app.core.security import (
    decode_refresh_token,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    hash_password,
)

from app.db.session import get_db
from app.models.user import User
from app.models.user_session import UserSession
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    AuthMessageResponse,
)


# ============================================================
# ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    login_data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):

    """
    Authenticate a user and create a new session.

    Both access and refresh tokens are issued after successful
    authentication.

    Only the SHA-256 hash of the refresh token is stored in
    the database.
    """

    # --------------------------------------------------------
    # STEP 1: Retrieve the account.
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == login_data.email)
        .first()
    )

    # Use a generic error to avoid revealing whether an account
    # exists or is inactive.
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --------------------------------------------------------
    # STEP 2: Verify the password.
    # --------------------------------------------------------

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --------------------------------------------------------
    # STEP 3: Calculate token expiration periods.
    # --------------------------------------------------------

    access_expiry = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    refresh_expiry = timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    current_time = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # STEP 4: Create a new session family.
    # --------------------------------------------------------

    session_family_id = uuid.uuid4()

    # Temporary values allow PostgreSQL to insert the session
    # and generate its identity session_id.
    #
    # These values are replaced with the real token hash and
    # JTI before the transaction is committed.

    temporary_refresh_hash = "0" * 64

    temporary_access_jti = uuid.uuid4()

    temporary_expiry = current_time + refresh_expiry

    try:
        # ----------------------------------------------------
        # STEP 5: Create the initial session record.
        # ----------------------------------------------------

        user_session = UserSession(
            session_family_id=session_family_id,
            user_id=user.user_id,
            refresh_token_hash=temporary_refresh_hash,
            access_token_jti=temporary_access_jti,
            expires_at=temporary_expiry,
        )

        db.add(user_session)

        # Flush sends the INSERT to PostgreSQL and retrieves
        # the generated session_id without committing.
        db.flush()

        session_id = user_session.session_id

        # ----------------------------------------------------
        # STEP 6: Generate the access token.
        # ----------------------------------------------------

        access_token, access_jti = create_access_token(
            user_id=user.user_id,
            session_id=session_id,
            expires_delta=access_expiry,
        )

        # ----------------------------------------------------
        # STEP 7: Generate the refresh token.
        # ----------------------------------------------------

        refresh_token, refresh_token_expires_at = (
            create_refresh_token(
                user_id=user.user_id,
                session_id=session_id,
                expires_delta=refresh_expiry,
            )
        )

        # ----------------------------------------------------
        # STEP 8: Store the real token identifiers.
        # ----------------------------------------------------

        user_session.refresh_token_hash = hash_refresh_token(
            refresh_token
        )

        user_session.access_token_jti = access_jti

        user_session.expires_at = refresh_token_expires_at

        # ----------------------------------------------------
        # STEP 9: Commit the session transaction.
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # STEP 10: Return the authentication tokens.
        # ----------------------------------------------------

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_expiry.total_seconds()),
            refresh_expires_in=int(refresh_expiry.total_seconds()),
        )

    except Exception:
        # If any database or token operation fails, remove
        # the uncommitted session changes.
        db.rollback()
        raise


# ============================================================
# OAUTH2 TOKEN ENDPOINT
# ============================================================

@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def oauth2_login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Authenticate using OAuth2 form-based credentials.

    OAuth2 uses:
        username: Registered employee email
        password: Account password

    The existing login function handles password verification,
    JWT generation, and database-backed session creation.
    """

    # Convert OAuth2 credentials into our existing login schema.
    login_data = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    # Reuse the existing authentication implementation.
    return login(
        login_data=login_data,
        db=db,
    )

# ============================================================
# REFRESH TOKEN ROTATION
# ============================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_tokens(
    refresh_data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Validate a refresh token and issue a replacement token pair.

    The previous session is revoked and linked to the new session.
    Reuse of a revoked refresh token revokes the entire session family.
    """

    # STEP 1: Validate the refresh token.

    payload = decode_refresh_token(refresh_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # STEP 2: Extract and validate token claims.

    try:
        user_id = int(payload.get("sub"))
        session_id = int(payload.get("sid"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )

    if user_id <= 0 or session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )

    supplied_hash = hash_refresh_token(
        refresh_data.refresh_token
    )

    try:
        # STEP 3: Lock the original session.

        old_session = (
            db.query(UserSession)
            .filter(
                UserSession.session_id == session_id,
                UserSession.user_id == user_id,
            )
            .with_for_update()
            .first()
        )

        if old_session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh session",
            )

        current_time = datetime.now(timezone.utc)

        # STEP 4: Detect reuse of a revoked refresh token.

        if old_session.revoked_at is not None:
            db.query(UserSession).filter(
                UserSession.session_family_id
                == old_session.session_family_id,
                UserSession.revoked_at.is_(None),
            ).update(
                {
                    UserSession.revoked_at: current_time
                },
                synchronize_session=False,
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected. Please log in again.",
            )

        # STEP 5: Validate the stored refresh-token hash.

        if old_session.refresh_token_hash != supplied_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # STEP 6: Check expiration.

        if old_session.expires_at <= current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        # STEP 7: Verify the account is active.

        user = (
            db.query(User)
            .filter(
                User.user_id == user_id,
                User.is_active.is_(True),
            )
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        # STEP 8: Calculate new expiration periods.

        access_expiry = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        refresh_expiry = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # STEP 9: Create a replacement session.

        new_session = UserSession(
            session_family_id=old_session.session_family_id,
            user_id=user.user_id,
            refresh_token_hash="0" * 64,
            access_token_jti=uuid.uuid4(),
            expires_at=current_time + refresh_expiry,
        )

        db.add(new_session)
        db.flush()

        # STEP 10: Generate replacement tokens.

        access_token, new_access_jti = create_access_token(
            user_id=user.user_id,
            session_id=new_session.session_id,
            expires_delta=access_expiry,
        )

        new_refresh_token, new_refresh_expiry = (
            create_refresh_token(
                user_id=user.user_id,
                session_id=new_session.session_id,
                expires_delta=refresh_expiry,
            )
        )

        # STEP 11: Store the replacement token identifiers.

        new_session.refresh_token_hash = hash_refresh_token(
            new_refresh_token
        )

        new_session.access_token_jti = new_access_jti
        new_session.expires_at = new_refresh_expiry

        # STEP 12: Revoke and link the previous session.

        old_session.revoked_at = current_time
        old_session.last_used_at = current_time

        old_session.replaced_by_session_id = new_session.session_id

        # STEP 13: Commit both session changes atomically.

        db.commit()

        # STEP 14: Return the replacement tokens.

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(access_expiry.total_seconds()),
            refresh_expires_in=int(refresh_expiry.total_seconds()),
        )

    except HTTPException:
        if db.in_transaction():
            db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

# ============================================================
# CURRENT USER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    """
    Return the profile of the currently authenticated user.

    Authentication is validated by get_current_user,
    including the database-backed session check.
    """

    return UserResponse(
        user_id=current_user.user_id,
        employee_id=current_user.employee_id,
        email=current_user.email,
        is_active=current_user.is_active,
        roles=[
            user_role.role.role_name
            for user_role in current_user.user_roles
        ],
    )

# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    authentication: Annotated[
        tuple[User, UserSession],
        Depends(get_current_user_and_session),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Revoke only the currently authenticated device session.

    Other active sessions belonging to the same user remain valid.
    """

    # STEP 1: Identify the authenticated session.

    current_user, current_session = authentication

    current_time = datetime.now(timezone.utc)

    # STEP 2: Explicitly update the matching database record.

    try:
        result = db.execute(
            update(UserSession)
            .where(
                UserSession.session_id == current_session.session_id,
                UserSession.user_id == current_user.user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=current_time,
                last_used_at=current_time,
            )
        )

        # Exactly one active session must be revoked.
        if result.rowcount != 1:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session could not be revoked",
            )

        # STEP 3: Commit the database transaction.

        db.commit()

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Successfully logged out",
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post(
    "/change-password",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Change the password of the currently authenticated user.

    Security behaviour:
        1. Verify the existing password.
        2. Validate the new password.
        3. Hash the new password using Argon2.
        4. Revoke all active sessions belonging to the user.
        5. Commit all changes atomically.

    The user must authenticate again after this operation.
    """

    # STEP 1: Verify the current password.

    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # STEP 2: Prevent reuse of the current password.

    if verify_password(
        password_data.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    # STEP 3: Hash the new password using Argon2.

    new_password_hash = hash_password(
        password_data.new_password
    )

    current_time = datetime.now(timezone.utc)

    # STEP 4: Update the password and revoke active sessions.

    try:
        current_user.password_hash = new_password_hash

        db.query(UserSession).filter(
            UserSession.user_id == current_user.user_id,
            UserSession.revoked_at.is_(None),
        ).update(
            {
                UserSession.revoked_at: current_time,
                UserSession.last_used_at: current_time,
            },
            synchronize_session=False,
        )

        # STEP 5: Commit both operations atomically.

        db.commit()

    except Exception:
        db.rollback()
        raise

    # STEP 6: Return confirmation.

    return AuthMessageResponse(
        message="Password changed successfully. Please log in again."
    )