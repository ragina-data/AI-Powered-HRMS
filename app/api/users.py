
"""
User Management API
===================

Purpose:
    Provide REST API endpoints for user account administration.

Responsibilities:
    1. Provision login accounts for existing employees.
    2. Enforce user.manage authorization.
    3. Return safe account information.

Security:
    Only authorized administrators can provision accounts.
    Passwords and password hashes are never returned.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.permissions import require_permission
from app.db.session import get_db
from app.models.user import User

from app.schemas.user import (
    UserAccountProvisionRequest,
    UserAccountProvisionResponse,
    UserAccountStatusUpdate,
    UserAccountStatusResponse,
)

from app.services.user_service import (
    provision_employee_account,
    update_user_account_status,
)


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


# ============================================================
# 1. PROVISION EMPLOYEE LOGIN ACCOUNT
# ============================================================

@router.post(
    "/employee-accounts",
    response_model=UserAccountProvisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def provision_employee_account_endpoint(
    account_data: UserAccountProvisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("user.manage")),
    ],
):
    """
    Create a login account for an existing employee.

    Requires:
        user.manage

    The employee's registered email is used automatically.

    The default employee role is assigned by the service.
    """

    return provision_employee_account(
        db=db,
        employee_id=account_data.employee_id,
        initial_password=account_data.initial_password,
        actor_user_id=current_user.user_id,
    )


# ============================================================
# 2. ACTIVATE / DEACTIVATE USER ACCOUNT
# ============================================================

@router.patch(
    "/{user_id}/status",
    response_model=UserAccountStatusResponse,
)
def change_user_account_status(
    user_id: Annotated[int, Path(gt=0)],
    status_data: UserAccountStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("user.manage")),
    ],
):
    """
    Activate or deactivate a user login account.

    Requires:
        user.manage

    Deactivation revokes all active login sessions.

    Activation requires the linked employee profile
    to be active.
    """

    return update_user_account_status(
        db=db,
        user_id=user_id,
        is_active=status_data.is_active,
        actor_user_id=current_user.user_id,
    )
