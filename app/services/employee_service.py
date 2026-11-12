
"""
Employee Service
================

Purpose:
    Implement business rules for Employee Management.

Responsibilities:
    1. Validate employee information.
    2. Validate department assignments.
    3. Validate reporting-manager assignments.
    4. Prevent duplicate employee and user emails.
    5. Create and update employee profiles.
    6. Record employee actions in the audit log.
    7. Manage database transactions safely.

Important:
    Login-account provisioning is handled separately
    through the user-management functionality.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.user_session import UserSession

from app.repositories.employee_repository import (
    create_employee_record,
    email_exists,
    get_department_by_id,
    get_employee_by_id,
    get_employee_by_email,
    get_manager_by_id,
    update_employee_record,
    get_employees,
)
from app.models.user import User


# ============================================================
# 1. DEPARTMENT VALIDATION
# ============================================================

def validate_department(
    db: Session,
    department_id: int,
) -> None:
    """Ensure the requested department exists and is active."""

    department = get_department_by_id(
        db,
        department_id,
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    if not department.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign an inactive department",
        )


# ============================================================
# 2. MANAGER VALIDATION
# ============================================================

def validate_manager(
    db: Session,
    manager_employee_id: int | None,
    employee_id: int | None = None,
) -> None:
    """
    Validate a reporting-manager assignment.

    Prevents:
        - Assigning a nonexistent manager.
        - Assigning an inactive manager.
        - Assigning an employee as their own manager.
        - Creating a circular reporting hierarchy.
    """

    if manager_employee_id is None:
        return

    if employee_id == manager_employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee cannot be their own manager",
        )

    manager = get_manager_by_id(
        db,
        manager_employee_id,
    )

    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting manager not found",
        )

    if not manager.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign an inactive employee as manager",
        )

    # Walk upward through the manager hierarchy.
    # The employee must not appear in this reporting chain.
    visited_ids = set()
    current_manager = manager

    while current_manager is not None:

        if employee_id is not None:
            if current_manager.employee_id == employee_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Circular reporting hierarchy is not allowed",
                )

        current_id = current_manager.employee_id

        if current_id in visited_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Existing circular reporting hierarchy detected",
            )

        visited_ids.add(current_id)

        if current_manager.manager_employee_id is None:
            break

        current_manager = get_employee_by_id(
            db,
            current_manager.manager_employee_id,
        )


# ============================================================
# 3. AUDIT LOGGING
# ============================================================

def create_employee_audit_log(
    db: Session,
    actor_user_id: int,
    action: str,
    employee: Employee,
    details: dict | None = None,
) -> None:
    """Record an employee operation in the audit log."""

    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type="Employee",
        entity_id=str(employee.employee_id),
        details=details or {},
    )

    db.add(audit_log)


# ============================================================
# 4. CREATE EMPLOYEE
# ============================================================

def create_employee(
    db: Session,
    employee_data: dict,
    actor_user_id: int,
) -> Employee:
    """
    Create a new employee profile.

    Login-account creation is intentionally excluded.
    """

    normalized_email = employee_data["email"].strip().lower()

    # Validate unique email across employees and users.
    if email_exists(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        )

    # Validate department.
    validate_department(
        db,
        employee_data["department_id"],
    )

    # Validate reporting manager.
    validate_manager(
        db,
        employee_data.get("manager_employee_id"),
    )

    employee_data = {
        **employee_data,
        "email": normalized_email,
    }

    try:
        employee = create_employee_record(
            db,
            employee_data,
        )

        create_employee_audit_log(
            db=db,
            actor_user_id=actor_user_id,
            action="EMPLOYEE_CREATED",
            employee=employee,
            details={
                "employee_code": employee.employee_code,
                "department_id": employee.department_id,
            },
        )

        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee record conflicts with existing database data",
        )

    except Exception:
        db.rollback()
        raise


# ============================================================
# 5. UPDATE EMPLOYEE
# ============================================================

def update_employee(
    db: Session,
    employee_id: int,
    update_data: dict,
    actor_user_id: int,
    can_manage_user_account: bool = False,
) -> Employee:
    """
    Update an existing employee profile.

    Email changes:
        If an employee has a linked login account, changing
        their email also changes the login email. This requires
        user.manage authorization.

    Employee status:
        Activation and deactivation are handled separately.
    """

    employee = get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # Generic profile updates cannot change employment status.
    if "is_active" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the employee status endpoint to change employee status",
        )

    # Validate the requested email.
    if "email" in update_data:

        normalized_email = update_data["email"].strip().lower()

        if normalized_email != employee.email.lower():

            if email_exists(
                db,
                normalized_email,
                exclude_employee_id=employee.employee_id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already registered",
                )

            # Keep employee and linked user emails consistent.
            if employee.user is not None:

                if not can_manage_user_account:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Changing the login email requires user management permission",
                    )

                employee.user.email = normalized_email

            update_data["email"] = normalized_email

    # Validate department changes.
    if "department_id" in update_data:

        department_id = update_data["department_id"]

        if department_id is not None:
            validate_department(
                db,
                department_id,
            )

    # Validate manager changes.
    if "manager_employee_id" in update_data:

        validate_manager(
            db,
            update_data["manager_employee_id"],
            employee.employee_id,
        )

    # Capture changed field names for audit purposes.
    changed_fields = sorted(update_data.keys())

    if not changed_fields:
        return employee

    try:
        updated_employee = update_employee_record(
            db,
            employee,
            update_data,
        )

        create_employee_audit_log(
            db=db,
            actor_user_id=actor_user_id,
            action="EMPLOYEE_UPDATED",
            employee=updated_employee,
            details={
                "changed_fields": changed_fields,
            },
        )

        db.commit()
        db.refresh(updated_employee)

        return updated_employee

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee update conflicts with existing database data",
        )

    except Exception:
        db.rollback()
        raise


# ============================================================
# 6. EMPLOYEE VISIBILITY AND ACCESS CONTROL
# ============================================================

def get_employee_visibility_scope(
    current_user: User,
) -> dict:
    """
    Determine which employee records the authenticated
    user is permitted to access.

    Access rules:
        Admin / HR:
            All employee records.

        Manager:
            Own profile and direct reports.

        Employee:
            Own profile only.

    Returns:
        Dictionary containing repository-level filters.
    """

    role_names = {
        user_role.role.role_name.lower()
        for user_role in current_user.user_roles
    }

    # Admin and HR have organization-wide visibility.
    if role_names.intersection({"admin", "hr"}):
        return {}

    # Managers can see themselves and their direct reports.
    if "manager" in role_names:

        if current_user.employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager account is not linked to an employee profile",
            )

        return {
            "reporting_scope_manager_id": current_user.employee_id,
        }

    # Employees can see only their own profile.
    if "employee" in role_names:

        if current_user.employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee account is not linked to an employee profile",
            )

        return {
            "employee_id": current_user.employee_id,
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access employee records",
    )


# ============================================================
# 7. GET AUTHORIZED EMPLOYEE LIST
# ============================================================

def get_employees_for_user(
    db: Session,
    current_user: User,
    search: str | None = None,
    department_id: int | None = None,
    manager_employee_id: int | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Employee], int]:
    """
    Retrieve employees within the authenticated user's
    permitted visibility scope.

    Authorization-based filtering is applied before
    pagination and database retrieval.
    """

    visibility_scope = get_employee_visibility_scope(
        current_user
    )

    return get_employees(
        db=db,
        search=search,
        department_id=department_id,
        manager_employee_id=manager_employee_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
        **visibility_scope,
    )


# ============================================================
# 8. GET AUTHORIZED EMPLOYEE BY ID
# ============================================================

def get_employee_for_user(
    db: Session,
    employee_id: int,
    current_user: User,
) -> Employee:
    """
    Retrieve one employee only when that employee falls
    within the authenticated user's visibility scope.

    Returns HTTP 404 when the employee is outside the
    permitted scope or does not exist.
    """

    visibility_scope = get_employee_visibility_scope(
        current_user
    )

    # An employee cannot request another employee's profile.
    own_employee_id = visibility_scope.get("employee_id")

    if (
        own_employee_id is not None
        and own_employee_id != employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    employees, _ = get_employees(
        db=db,
        employee_id=employee_id,
        reporting_scope_manager_id=visibility_scope.get(
            "reporting_scope_manager_id"
        ),
        limit=1,
    )

    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employees[0]


# ============================================================
# 9. ACTIVATE / DEACTIVATE EMPLOYEE
# ============================================================

def update_employee_status(
    db: Session,
    employee_id: int,
    is_active: bool,
    actor_user_id: int,
) -> Employee:
    """
    Activate or deactivate an employee.

    Deactivation:
        1. Mark employee as inactive.
        2. Disable the linked user account.
        3. Revoke all active login sessions.
        4. Record the operation in the audit log.

    Activation:
        1. Mark employee as active.
        2. Keep the linked user account inactive.
        3. Require a separate authorized account activation
           before the employee can log in.

    All database changes are committed atomically.
    """

    # STEP 1: Retrieve the employee.

    employee = get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    current_time = datetime.now(timezone.utc)
    previous_status = employee.is_active

    linked_user = employee.user

    try:

        # STEP 2: Update employee employment status.

        employee.is_active = is_active
        employee.updated_at = current_time

        user_status_changed = False
        revoked_session_count = 0

        # STEP 3: Handle linked login account.

        if not is_active and linked_user is not None:

            if linked_user.is_active:
                linked_user.is_active = False
                linked_user.updated_at = current_time
                user_status_changed = True

            # STEP 4: Revoke all active sessions.

            revoked_session_count = (
                db.query(UserSession)
                .filter(
                    UserSession.user_id == linked_user.user_id,
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

        # STEP 5: Check whether anything changed.

        employee_status_changed = previous_status != is_active

        if not (
            employee_status_changed
            or user_status_changed
            or revoked_session_count
        ):
            return employee

        # STEP 6: Create audit log.

        action = (
            "EMPLOYEE_ACTIVATED"
            if is_active
            else "EMPLOYEE_DEACTIVATED"
        )

        create_employee_audit_log(
            db=db,
            actor_user_id=actor_user_id,
            action=action,
            employee=employee,
            details={
                "previous_status": previous_status,
                "new_status": is_active,
                "login_account_disabled": (
                    linked_user is not None and not is_active
                ),
                "login_account_reactivated": False,
                "sessions_revoked": revoked_session_count,
            },
        )

        # STEP 7: Commit all changes atomically.

        db.commit()
        db.refresh(employee)

        return employee

    except Exception:
        db.rollback()
        raise
