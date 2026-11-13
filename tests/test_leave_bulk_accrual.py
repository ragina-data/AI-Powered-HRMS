
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.leave_service import (
    accrue_annual_leave_for_all_active_employees,
)


def create_employee(
    employee_id,
    hire_date,
):
    return SimpleNamespace(
        employee_id=employee_id,
        employee_code=f"EMP{employee_id:03d}",
        hire_date=hire_date,
    )


def test_bulk_accrual_processes_eligible_employees():

    db = MagicMock()

    employees = [
        create_employee(1, date(2026, 1, 1)),
        create_employee(2, date(2026, 2, 1)),
        create_employee(3, date(2026, 12, 1)),
    ]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 3),
        ),
        patch(
            "app.services.leave_service.accrue_annual_leave_for_employee",
            return_value={"status": "success"},
        ) as accrue,
    ):

        result = accrue_annual_leave_for_all_active_employees(
            db=db,
            as_of_date=date(2026, 11, 12),
        )

    assert result["total_active_employees"] == 3
    assert result["total_processed"] == 2
    assert result["total_failed"] == 0
    assert result["future_hires_skipped"] == 1

    assert accrue.call_count == 2


def test_bulk_accrual_skips_missing_hire_dates():

    db = MagicMock()

    employees = [
        create_employee(1, date(2026, 1, 1)),
        create_employee(2, None),
    ]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 2),
        ),
        patch(
            "app.services.leave_service.accrue_annual_leave_for_employee",
            return_value={"status": "success"},
        ) as accrue,
    ):

        result = accrue_annual_leave_for_all_active_employees(
            db=db,
            as_of_date=date(2026, 11, 12),
        )

    assert result["total_processed"] == 1
    assert result["missing_hire_dates_skipped"] == 1

    accrue.assert_called_once()


def test_bulk_accrual_continues_after_employee_failure():

    db = MagicMock()

    employees = [
        create_employee(1, date(2026, 1, 1)),
        create_employee(2, date(2026, 2, 1)),
    ]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 2),
        ),
        patch(
            "app.services.leave_service.accrue_annual_leave_for_employee",
            side_effect=[
                RuntimeError("Employee accrual failed"),
                {"status": "success"},
            ],
        ) as accrue,
    ):

        result = accrue_annual_leave_for_all_active_employees(
            db=db,
            as_of_date=date(2026, 11, 12),
        )

    assert result["total_processed"] == 1
    assert result["total_failed"] == 1

    assert accrue.call_count == 2
    db.rollback.assert_called_once()


def test_bulk_accrual_supports_pagination():

    db = MagicMock()

    first_batch = [
        create_employee(1, date(2026, 1, 1)),
        create_employee(2, date(2026, 2, 1)),
    ]

    second_batch = [
        create_employee(3, date(2026, 3, 1)),
    ]

    with (
        patch(
            "app.services.leave_service.get_employees",
            side_effect=[
                (first_batch, 3),
                (second_batch, 3),
            ],
        ) as get_employees,
        patch(
            "app.services.leave_service.accrue_annual_leave_for_employee",
            return_value={"status": "success"},
        ) as accrue,
    ):

        result = accrue_annual_leave_for_all_active_employees(
            db=db,
            as_of_date=date(2026, 11, 12),
            batch_size=2,
        )

    assert result["total_processed"] == 3
    assert result["total_failed"] == 0

    assert get_employees.call_count == 2
    assert accrue.call_count == 3

    assert get_employees.call_args_list[0].kwargs["skip"] == 0
    assert get_employees.call_args_list[1].kwargs["skip"] == 2
