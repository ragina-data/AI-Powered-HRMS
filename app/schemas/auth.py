
from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# LOGIN REQUEST
# --------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Registered employee email address"
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Account password"
    )


# --------------------------------------------------
# TOKEN RESPONSE
# --------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        ...,
        gt=0,
        description="Token expiration time in seconds"
    )


# --------------------------------------------------
# USER RESPONSE
# --------------------------------------------------

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    employee_id: int
    email: str
    is_active: bool
    roles: list[str] = Field(default_factory=list)
