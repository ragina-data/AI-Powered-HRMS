
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.employee_service import (
    get_employee_for_user,
    get_employees_for_user,
)


def serialize_employee(employee) -> dict:
    """
    Convert an Employee ORM object into a JSON-compatible dictionary.
    """

    return {
        "employee_id": employee.employee_id,
        "employee_code": employee.employee_code,
        "full_name": employee.full_name,
        "email": employee.email,
        "department": employee.department,
        "department_id": employee.department_id,
        "job_title": employee.job_title,
        "hire_date": (
            employee.hire_date.isoformat()
            if employee.hire_date
            else None
        ),
        "manager_employee_id": employee.manager_employee_id,
        "is_active": employee.is_active,
    }


# ============================================================
# 1. GET MY EMPLOYEE PROFILE
# ============================================================

def get_my_employee_profile(
    db: Session,
    current_user: User,
) -> dict:
    """
    Retrieve the authenticated employee's own profile.
    """

    if current_user.employee_id is None:
        raise ValueError(
            "Your user account is not linked to an employee profile."
        )

    employee = get_employee_for_user(
        db=db,
        employee_id=current_user.employee_id,
        current_user=current_user,
    )

    return serialize_employee(employee)


# ============================================================
# 2. GET AUTHORIZED EMPLOYEE PROFILE
# ============================================================

def get_authorized_employee_profile(
    db: Session,
    current_user: User,
    employee_id: int,
) -> dict:
    """
    Retrieve an employee profile within the authenticated
    user's authorized visibility scope.
    """

    employee = get_employee_for_user(
        db=db,
        employee_id=employee_id,
        current_user=current_user,
    )

    return serialize_employee(employee)


# ============================================================
# 3. SEARCH AUTHORIZED EMPLOYEES
# ============================================================

def search_authorized_employees(
    db: Session,
    current_user: User,
    search: str | None = None,
    department_id: int | None = None,
    manager_employee_id: int | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """
    Search employees within the authenticated user's
    authorized visibility scope.

    The employee service applies authorization filters
    before retrieving and paginating the results.
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

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "employees": [
            serialize_employee(employee)
            for employee in employees
        ],
    }
