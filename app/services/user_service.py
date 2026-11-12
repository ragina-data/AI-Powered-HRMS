
"""
User Service
============

Purpose:
    Implement business rules for user account provisioning.

Responsibilities:
    1. Validate employee eligibility for account provisioning.
    2. Prevent duplicate login accounts.
    3. Prevent duplicate login email addresses.
    4. Hash initial passwords using Argon2.
    5. Assign the default employee role.
    6. Record account creation in the audit log.
    7. Manage database transactions safely.

Security:
    - Plain-text passwords are never stored.
    - Password hashes are never included in API responses.
    - Role assignment uses existing RBAC records.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit_log import AuditLog

from datetime import datetime, timezone

from app.models.user_session import UserSession
from app.repositories.employee_repository import (
    get_employee_by_id,
)

from app.repositories.user_repository import (
    get_user_by_id,
    get_user_by_employee_id,
    get_user_by_email,
    get_role_by_name,
    create_user_record,
    create_user_role_assignment,
)


# ============================================================
# 1. PROVISION EMPLOYEE LOGIN ACCOUNT
# ============================================================

def provision_employee_account(
    db: Session,
    employee_id: int,
    initial_password: str,
    actor_user_id: int,
) -> dict:
    """
    Create a login account for an existing active employee.

    Workflow:
        1. Retrieve employee.
        2. Verify employee is active.
        3. Check for an existing linked account.
        4. Check login email uniqueness.
        5. Retrieve the existing employee role.
        6. Hash the initial password using Argon2.
        7. Create the user account.
        8. Assign the employee role.
        9. Create an audit record.
       10. Commit all operations atomically.

    Returns:
        A dictionary containing safe account information.
        Passwords and password hashes are never returned.
    """

    # --------------------------------------------------------
    # STEP 1: Retrieve the employee.
    # --------------------------------------------------------

    employee = get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # --------------------------------------------------------
    # STEP 2: Only active employees can receive login accounts.
    # --------------------------------------------------------

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provision an account for an inactive employee",
        )

    # --------------------------------------------------------
    # STEP 3: Check for an existing linked login account.
    # --------------------------------------------------------

    existing_user = get_user_by_employee_id(
        db,
        employee_id,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee already has a login account",
        )

    # --------------------------------------------------------
    # STEP 4: Validate login email uniqueness.
    # --------------------------------------------------------

    normalized_email = employee.email.strip().lower()

    existing_email_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_email_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered to another user",
        )

    # --------------------------------------------------------
    # STEP 5: Retrieve the existing employee role.
    # --------------------------------------------------------

    employee_role = get_role_by_name(
        db,
        "employee",
    )

    if employee_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default employee role is not configured",
        )

    # --------------------------------------------------------
    # STEP 6: Hash password and perform database operations.
    # --------------------------------------------------------

    try:

        password_hash = hash_password(
            initial_password
        )

        # Create the login account.
        user = create_user_record(
            db,
            {
                "employee_id": employee.employee_id,
                "email": normalized_email,
                "password_hash": password_hash,
                "is_active": True,
            },
        )

        # Assign the existing employee role.
        create_user_role_assignment(
            db,
            user_id=user.user_id,
            role_id=employee_role.role_id,
        )

        # Create account provisioning audit record.
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action="USER_ACCOUNT_CREATED",
            entity_type="User",
            entity_id=str(user.user_id),
            details={
                "employee_id": employee.employee_id,
                "employee_code": employee.employee_code,
                "role_name": "employee",
            },
        )

        db.add(audit_log)

        # Commit account, role and audit record together.
        db.commit()
        db.refresh(user)

        # Return safe account information.
        return {
            "user_id": user.user_id,
            "employee_id": user.employee_id,
            "email": user.email,
            "is_active": user.is_active,
            "role_name": employee_role.role_name,
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account provisioning conflicts with existing database data",
        )

    except Exception:
        db.rollback()
        raise


# ============================================================
# 2. ACTIVATE / DEACTIVATE USER ACCOUNT
# ============================================================

def update_user_account_status(
    db: Session,
    user_id: int,
    is_active: bool,
    actor_user_id: int,
) -> dict:
    """
    Activate or deactivate a user login account.

    Activation:
        1. Retrieve the user account.
        2. Verify that a linked employee is active.
        3. Activate the login account.
        4. Do not restore previously revoked sessions.

    Deactivation:
        1. Deactivate the login account.
        2. Revoke all active login sessions.
        3. Record the operation in the audit log.

    All database changes are committed atomically.
    """

    # STEP 1: Retrieve user account.

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found",
        )

    # STEP 2: Validate linked employee before activation.

    if is_active and user.employee_id is not None:

        employee = user.employee

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked employee profile not found",
            )

        if not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot activate login account for an inactive employee",
            )

    current_time = datetime.now(timezone.utc)
    previous_status = user.is_active

    try:

        # STEP 3: Update user account status.

        user.is_active = is_active

        status_changed = previous_status != is_active

        if status_changed:
            user.updated_at = current_time

        sessions_revoked = 0

        # STEP 4: Revoke all active sessions on deactivation.

        if not is_active:

            sessions_revoked = (
                db.query(UserSession)
                .filter(
                    UserSession.user_id == user.user_id,
                    UserSession.revoked_at.is_(None),
                )
                .update(
                    {
                        UserSession.revoked_at: current_time,
                        UserSession.last_used_at: current_time,
                    },
                    synchronize_session=False,
                )
            )

        # STEP 5: Avoid unnecessary audit records.

        if not status_changed and sessions_revoked == 0:
            return {
                "user_id": user.user_id,
                "employee_id": user.employee_id,
                "email": user.email,
                "is_active": user.is_active,
                "sessions_revoked": 0,
            }

        # STEP 6: Create audit record.

        action = (
            "USER_ACCOUNT_ACTIVATED"
            if is_active
            else "USER_ACCOUNT_DEACTIVATED"
        )

        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type="User",
            entity_id=str(user.user_id),
            details={
                "previous_status": previous_status,
                "new_status": is_active,
                "employee_id": user.employee_id,
                "sessions_revoked": sessions_revoked,
            },
        )

        db.add(audit_log)

        # STEP 7: Commit transaction.

        db.commit()
        db.refresh(user)

        return {
            "user_id": user.user_id,
            "employee_id": user.employee_id,
            "email": user.email,
            "is_active": user.is_active,
            "sessions_revoked": sessions_revoked,
        }

    except Exception:
        db.rollback()
        raise
