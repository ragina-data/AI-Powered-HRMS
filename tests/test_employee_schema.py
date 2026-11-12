
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeStatusUpdate,
)


def test_employee_create_valid_data():
    employee = EmployeeCreate(
        full_name="Alex Morgan",
        email="alex.morgan@example.com",
        department_id=1,
        job_title="HR Coordinator",
        hire_date=date(2026, 11, 12),
        manager_employee_id=1,
    )

    assert employee.full_name == "Alex Morgan"
    assert employee.department_id == 1


def test_employee_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        EmployeeCreate(
            full_name="Alex Morgan",
            email="invalid-email",
            department_id=1,
            job_title="HR Coordinator",
            hire_date=date(2026, 11, 12),
        )


def test_employee_update_supports_partial_updates():
    employee = EmployeeUpdate(
        full_name="Alex Morgan",
    )

    assert employee.model_dump(exclude_unset=True) == {
        "full_name": "Alex Morgan"
    }


@pytest.mark.parametrize("field", ["full_name", "email"])
def test_employee_update_rejects_null_required_fields(field):
    with pytest.raises(ValidationError):
        EmployeeUpdate(**{field: None})


def test_employee_update_allows_nullable_department():
    employee = EmployeeUpdate(department_id=None)

    assert employee.department_id is None


def test_employee_status_update():
    inactive = EmployeeStatusUpdate(is_active=False)
    active = EmployeeStatusUpdate(is_active=True)

    assert inactive.is_active is False
    assert active.is_active is True


def test_employee_list_response():
    response = EmployeeListResponse(
        items=[],
        total=50,
        skip=0,
        limit=20,
    )

    assert response.total == 50
    assert response.skip == 0
    assert response.limit == 20
    assert response.items == []
