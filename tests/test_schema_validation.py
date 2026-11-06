from datetime import date

from pydantic import ValidationError

from app.schemas import (
    EmployeeCreate,
    LeaveRequestCreate,
    TimesheetCreate,
    TimesheetEntryCreate,
)


def test_invalid_email():
    try:
        EmployeeCreate(
            full_name="Test Employee",
            email="invalid-email",
            department_id=1,
            job_title="Analyst",
            hire_date=date.today(),
        )
        assert False, "Invalid email was accepted"
    except ValidationError:
        print("PASS: Invalid email rejected")


def test_invalid_leave_dates():
    try:
        LeaveRequestCreate(
            leave_type="annual",
            start_date=date(2026, 11, 15),
            end_date=date(2026, 11, 10),
        )
        assert False, "Invalid leave dates were accepted"
    except ValidationError:
        print("PASS: Invalid leave dates rejected")


def test_timesheet_entry_outside_period():
    try:
        TimesheetCreate(
            period_start=date(2026, 11, 1),
            period_end=date(2026, 11, 7),
            entries=[
                TimesheetEntryCreate(
                    work_date=date(2026, 11, 10),
                    hours_worked=8,
                )
            ],
        )
        assert False, "Invalid timesheet entry was accepted"
    except ValidationError:
        print("PASS: Timesheet entry outside period rejected")