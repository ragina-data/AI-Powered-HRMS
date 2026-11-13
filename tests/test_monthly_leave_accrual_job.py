
from unittest.mock import MagicMock

from app.db import session as db_session
from app.services import leave_service

from scripts import run_monthly_leave_accrual as job


def successful_result():
    return {
        "total_active_employees": 49,
        "total_processed": 49,
        "total_failed": 0,
        "future_hires_skipped": 4,
        "missing_hire_dates_skipped": 0,
        "employee_errors": [],
    }


def test_monthly_job_completes_successfully(monkeypatch):

    db = MagicMock()

    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        leave_service,
        "accrue_annual_leave_for_all_active_employees",
        lambda **kwargs: successful_result(),
    )

    result = job.main(["--execute"])

    assert result == 0
    db.close.assert_called_once()


def test_monthly_job_reports_employee_failures(monkeypatch):

    db = MagicMock()

    failed_result = successful_result()
    failed_result["total_failed"] = 1
    failed_result["total_processed"] = 48
    failed_result["employee_errors"] = [
        {
            "employee_id": 10,
            "error": "Test accrual failure",
        }
    ]

    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        leave_service,
        "accrue_annual_leave_for_all_active_employees",
        lambda **kwargs: failed_result,
    )

    result = job.main(["--execute"])

    assert result == 1
    db.close.assert_called_once()


def test_monthly_job_handles_unexpected_errors(monkeypatch):

    db = MagicMock()

    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        lambda: db,
    )

    def raise_error(**kwargs):
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr(
        leave_service,
        "accrue_annual_leave_for_all_active_employees",
        raise_error,
    )

    result = job.main(["--execute"])

    assert result == 1
    db.close.assert_called_once()

def test_monthly_job_dry_run_does_not_execute_accrual(monkeypatch):

    from decimal import Decimal

    db = MagicMock()

    preview_result = {
        "total_active_employees": 53,
        "employees_previewed": 49,
        "future_hires_skipped": 4,
        "missing_hire_dates_skipped": 0,
        "manual_review_required": 0,
        "total_proposed_credit_days": Decimal("0"),
    }

    monkeypatch.setattr(
        db_session,
        "SessionLocal",
        lambda: db,
    )

    monkeypatch.setattr(
        leave_service,
        "preview_annual_leave_accrual_for_all_active_employees",
        lambda **kwargs: preview_result,
    )

    accrual = MagicMock()

    monkeypatch.setattr(
        leave_service,
        "accrue_annual_leave_for_all_active_employees",
        accrual,
    )

    result = job.main(["--dry-run"])

    assert result == 0
    accrual.assert_not_called()
    db.close.assert_called_once()
