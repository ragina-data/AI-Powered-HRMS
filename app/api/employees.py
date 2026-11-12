
"""
Employee Management API
=======================

Purpose:
    Provide REST API endpoints for employee management.

Responsibilities:
    1. Create employee profiles.
    2. Retrieve authorized employee records.
    3. List and search employees with pagination.
    4. Update employee information.
    5. Enforce permission-based access control.

Note:
    Login-account provisioning is separate from employee
    profile creation.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.permissions import (
    require_permission,
    user_has_permission,
)
from app.db.session import get_db
from app.models.user import User

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeStatusUpdate,
)

from app.services.employee_service import (
    create_employee,
    update_employee,
    get_employees_for_user,
    get_employee_for_user,
    update_employee_status,
)


router = APIRouter(
    prefix="/employees",
    tags=["Employee Management"],
)


# ============================================================
# 1. CREATE EMPLOYEE
# ============================================================

@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_endpoint(
    employee_data: EmployeeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("employee.manage")),
    ],
):
    """
    Create a new employee profile.

    Requires:
        employee.manage

    Creates an employee profile only.
    Login-account provisioning is handled separately.
    """

    return create_employee(
        db=db,
        employee_data=employee_data.model_dump(),
        actor_user_id=current_user.user_id,
    )


# ============================================================
# 2. LIST EMPLOYEES
# ============================================================

@router.get(
    "/",
    response_model=EmployeeListResponse,
)
def list_employees(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "employee.read_self",
                "employee.read_team",
            )
        ),
    ],
    search: str | None = Query(default=None, max_length=100),
    department_id: int | None = Query(default=None, gt=0),
    manager_employee_id: int | None = Query(default=None, gt=0),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Retrieve employees according to the current user's
    authorized visibility scope.

    Admin / HR:
        All employees.

    Manager:
        Own profile and direct reports.

    Employee:
        Own profile only.
    """

    employees, total = get_employees_for_user(
        db=db,
        current_user=current_user,
        search=search,
        department_id=department_id,
        manager_employee_id=manager_employee_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )

    return EmployeeListResponse(
        items=employees,
        total=total,
        skip=skip,
        limit=limit,
    )


# ============================================================
# 3. GET OWN EMPLOYEE PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=EmployeeResponse,
)
def get_my_employee_profile(
    current_user: Annotated[
        User,
        Depends(require_permission("employee.read_self")),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve the authenticated user's own employee profile."""

    if current_user.employee_id is None:


        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found",
        )

    return get_employee_for_user(
        db=db,
        employee_id=current_user.employee_id,
        current_user=current_user,
    )


# ============================================================
# 4. GET EMPLOYEE BY ID
# ============================================================

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def get_employee_endpoint(
    employee_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "employee.read_self",
                "employee.read_team",
            )
        ),
    ],
):
    """
    Retrieve an employee by ID.

    The service layer enforces employee visibility restrictions.
    """

    return get_employee_for_user(
        db=db,
        employee_id=employee_id,
        current_user=current_user,
    )

# ============================================================
# 5. UPDATE EMPLOYEE
# ============================================================

@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee_endpoint(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("employee.manage")),
    ],
):
    """
    Update an employee profile.

    Requires:
        employee.manage

    Changing a linked login email additionally requires
    user.manage.
    """

    update_data = employee_data.model_dump(
        exclude_unset=True,
    )

    can_manage_user_account = user_has_permission(
        db=db,
        user_id=current_user.user_id,
        permission_code="user.manage",
    )

    return update_employee(
        db=db,
        employee_id=employee_id,
        update_data=update_data,
        actor_user_id=current_user.user_id,
        can_manage_user_account=can_manage_user_account,
    )

# ============================================================
# 6. ACTIVATE / DEACTIVATE EMPLOYEE
# ============================================================

@router.patch(
    "/{employee_id}/status",
    response_model=EmployeeResponse,
)
def change_employee_status(
    employee_id: int,
    status_data: EmployeeStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("employee.manage")),
    ],
):
    """
    Activate or deactivate an employee.

    Requires:
        employee.manage

    Deactivation also disables the linked login account
    and revokes all active sessions.
    """

    return update_employee_status(
        db=db,
        employee_id=employee_id,
        is_active=status_data.is_active,
        actor_user_id=current_user.user_id,
    )

