"""
User Management Schemas
=======================

Purpose:
    Define request and response validation for user accounts.

Responsibilities:
    1. Validate account provisioning requests.
    2. Validate the initial password.
    3. Define safe user account responses.

Security:
    Password hashes and plain-text passwords must never
    appear in API responses.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


# --------------------------------------------------
# USER ACCOUNT PROVISION REQUEST
# --------------------------------------------------

class UserAccountProvisionRequest(BaseModel):
    employee_id: int = Field(gt=0)

    initial_password: str = Field(
        min_length=8,
        max_length=128,
        description="Initial password for the employee login account",
    )


# --------------------------------------------------
# USER ACCOUNT RESPONSE
# --------------------------------------------------

class UserAccountProvisionResponse(BaseModel):
    user_id: int
    employee_id: int
    email: EmailStr
    is_active: bool
    role_name: str

# --------------------------------------------------
# USER ACCOUNT STATUS UPDATE
# --------------------------------------------------

class UserAccountStatusUpdate(BaseModel):
    """
    Request schema for activating or deactivating
    a user login account.
    """

    is_active: bool

# --------------------------------------------------
# USER ACCOUNT STATUS RESPONSE
# --------------------------------------------------

class UserAccountStatusResponse(BaseModel):
    user_id: int
    employee_id: int | None
    email: EmailStr
    is_active: bool
    sessions_revoked: int = Field(ge=0)