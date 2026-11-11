
"""
Authentication Schemas
======================

Purpose:
    Define request and response validation models for authentication.

Includes:
    1. Login request.
    2. Token response.
    3. Refresh-token request.
    4. Password-change request.
    5. Standard authentication message response.
    6. Authenticated user profile response.
"""

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# 1. LOGIN REQUEST
# ============================================================

class LoginRequest(BaseModel):
    """Credentials submitted by a user during login."""

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Registered employee email address",
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Account password",
    )


# ============================================================
# 2. TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):
    """
    Authentication tokens returned after successful login
    or refresh-token rotation.
    """

    access_token: str

    refresh_token: str

    token_type: str = "bearer"

    expires_in: int = Field(
        ...,
        gt=0,
        description="Access-token expiration time in seconds",
    )

    refresh_expires_in: int = Field(
        ...,
        gt=0,
        description="Refresh-token expiration time in seconds",
    )


# ============================================================
# 3. REFRESH TOKEN REQUEST
# ============================================================

class RefreshTokenRequest(BaseModel):
    """Refresh token submitted to obtain new authentication tokens."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Valid refresh token",
    )


# ============================================================
# 4. CHANGE PASSWORD REQUEST
# ============================================================

class ChangePasswordRequest(BaseModel):
    """Credentials required to change the current user's password."""

    current_password: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Current account password",
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)",
    )


# ============================================================
# 5. AUTHENTICATION MESSAGE RESPONSE
# ============================================================

class AuthMessageResponse(BaseModel):
    """Standard response for logout and password-change operations."""

    message: str


# ============================================================
# 6. AUTHENTICATED USER RESPONSE
# ============================================================

class UserResponse(BaseModel):
    """Profile information for the currently authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int

    employee_id: int | None

    email: str

    is_active: bool

    roles: list[str] = Field(default_factory=list)
