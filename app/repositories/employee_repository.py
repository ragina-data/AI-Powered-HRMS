
"""
Employee Repository
===================

Purpose:
    Centralize database queries for employee records.

Responsibilities:
    1. Retrieve employees by ID.
    2. Retrieve employees by email.
    3. Search and list employees.
    4. Support department and manager filtering.
    5. Keep database transaction management in the service layer.
"""
from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User


def get_employee_by_id(
    db: Session,
    employee_id: int,
) -> Employee | None:
    """Retrieve one employee by primary key."""

    return (
        db.query(Employee)
        .options(
            joinedload(Employee.department_info),
            joinedload(Employee.manager),
        )
        .filter(Employee.employee_id == employee_id)
        .first()
    )


def get_employee_by_email(
    db: Session,
    email: str,
) -> Employee | None:
    """Retrieve an employee using a case-insensitive email lookup."""

    normalized_email = email.strip().lower()

    return (
        db.query(Employee)
        .filter(
            Employee.email.ilike(normalized_email)
        )
        .first()
    )


def get_employees(
    db: Session,
    search: str | None = None,
    department_id: int | None = None,
    manager_employee_id: int | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    employee_id: int | None = None,
    reporting_scope_manager_id: int | None = None,
) -> tuple[list[Employee], int]:
    """
    Retrieve employees with filtering and pagination.

    Returns:
        A tuple containing:
            1. Employee records.
            2. Total number of matching records.

    Note:
        The service layer is responsible for applying
        authorization-based filters before calling this
        repository function.
    """

    query = (
        db.query(Employee)
        .options(
            joinedload(Employee.department_info),
            joinedload(Employee.manager),
        )
    )

    # Search employee name, email, or employee code.
    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Employee.full_name.ilike(search_term),
                Employee.email.ilike(search_term),
                Employee.employee_code.ilike(search_term),
            )
        )

    # Filter by department.
    if department_id is not None:
        query = query.filter(
            Employee.department_id == department_id
        )

    # Restrict results to an authorized manager's direct reports.
    if manager_employee_id is not None:
        query = query.filter(
            Employee.manager_employee_id == manager_employee_id
        )
        # Restrict results to one specific employee.
    if employee_id is not None:
        query = query.filter(
            Employee.employee_id == employee_id
        )

    # Include a manager's own profile and direct reports.
    if reporting_scope_manager_id is not None:
        query = query.filter(
            or_(
                Employee.employee_id == reporting_scope_manager_id,
                Employee.manager_employee_id == reporting_scope_manager_id,
            )
        )

    # Filter by active/inactive status.
    if is_active is not None:
        query = query.filter(
            Employee.is_active.is_(is_active)
        )

    total = query.count()

    employees = (
        query
        .order_by(Employee.employee_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return employees, total


def get_department_by_id(
    db: Session,
    department_id: int,
) -> Department | None:
    """Retrieve a department by ID."""

    return (
        db.query(Department)
        .filter(Department.department_id == department_id)
        .first()
    )


def get_manager_by_id(
    db: Session,
    manager_employee_id: int,
) -> Employee | None:
    """Retrieve an employee who may be assigned as a manager."""


    return (
        db.query(Employee)
        .filter(Employee.employee_id == manager_employee_id)
        .first()
    )


def email_exists(
    db: Session,
    email: str,
    exclude_employee_id: int | None = None,
) -> bool:
    """
    Check whether an email is already used by another
    employee or user account.

    Excludes the employee and their own linked account
    when checking an employee update.
    """

    normalized_email = email.strip().lower()

    employee_query = db.query(Employee.employee_id).filter(
        func.lower(Employee.email) == normalized_email
    )

    if exclude_employee_id is not None:
        employee_query = employee_query.filter(
            Employee.employee_id != exclude_employee_id
        )

    if employee_query.first() is not None:
        return True

    user_query = db.query(User.user_id).filter(
        func.lower(User.email) == normalized_email
    )

    if exclude_employee_id is not None:
        user_query = user_query.filter(
            or_(
                User.employee_id.is_(None),
                User.employee_id != exclude_employee_id,
            )
        )

    return user_query.first() is not None


def create_employee_record(
    db: Session,
    employee_data: dict,
) -> Employee:
    """
    Add a new employee record and flush it to PostgreSQL.

    Transaction commit is intentionally handled by the service.
    """

    employee = Employee(**employee_data)

    db.add(employee)
    db.flush()
    db.refresh(employee)

    return employee


def update_employee_record(
    db: Session,
    employee: Employee,
    update_data: dict,
) -> Employee:
    """
    Apply validated employee changes and flush them.

    Transaction commit is intentionally handled by the service.
    """

    for field, value in update_data.items():
        setattr(employee, field, value)

    employee.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(employee)

    return employee
