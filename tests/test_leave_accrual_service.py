
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.leave_service import (
    accrue_annual_leave_for_employee,
)


# ============================================================
# TEST HELPERS
# ============================================================

def create_employee():
    return SimpleNamespace(
        employee_id=10,
        employee_code="EMP010",
        is_active=True,
        hire_date=date(2026, 1, 1),
    )


def create_balance(
    balance_id,
    entitlement_days,
    used_days=Decimal("0"),
):
    return SimpleNamespace(
        leave_balance_id=balance_id,
        entitlement_days=Decimal(str(entitlement_days)),
        used_days=Decimal(str(used_days)),
    )


# ============================================================
# 1. TEST MONTHLY ACCRUAL
# ============================================================

def test_monthly_accrual_credits_correct_days():

    employee = create_employee()

    balance = create_balance(
        balance_id=101,
        entitlement_days="12",
    )

    db = MagicMock()

    with (
        patch(
            "app.services.leave_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.leave_service.get_or_create_employee_leave_balance_for_update",
            return_value=balance,
        ),
        patch(
            "app.services.leave_service.create_leave_transaction",
        ) as create_transaction,
        patch(
            "app.services.leave_service.record_leave_audit",
        ) as record_audit,
    ):

        result = accrue_annual_leave_for_employee(
            db=db,
            employee_id=10,
            as_of_date=date(2026, 8, 1),
        )

    assert balance.entitlement_days == Decimal("14")

    assert (
        result["current_service_year"]["additional_credit"]
        == Decimal("2")
    )

    assert result["current_service_year"]["available_days"] == Decimal("14")

    create_transaction.assert_called_once()
    record_audit.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(balance)


# ============================================================
# 2. TEST DUPLICATE ACCRUAL PREVENTION
# ============================================================

def test_repeated_accrual_does_not_duplicate_credit():

    employee = create_employee()

    balance = create_balance(
        balance_id=101,
        entitlement_days="12",
    )

    db = MagicMock()

    with (
        patch(
            "app.services.leave_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.leave_service.get_or_create_employee_leave_balance_for_update",
            return_value=balance,
        ),
        patch(
            "app.services.leave_service.create_leave_transaction",
        ) as create_transaction,
        patch(
            "app.services.leave_service.record_leave_audit",
        ) as record_audit,
    ):

        first_result = accrue_annual_leave_for_employee(
            db=db,
            employee_id=10,
            as_of_date=date(2026, 8, 1),
        )

        second_result = accrue_annual_leave_for_employee(
            db=db,
            employee_id=10,
            as_of_date=date(2026, 8, 1),
        )

    assert first_result["current_service_year"]["additional_credit"] == Decimal("2")

    assert second_result["current_service_year"]["additional_credit"] == Decimal("0")

    assert balance.entitlement_days == Decimal("14")

    # Only one credit transaction should exist.
    create_transaction.assert_called_once()

    # Only one accrual audit event should exist.
    record_audit.assert_called_once()

    assert db.commit.call_count == 2


# ============================================================
# 3. TEST FIRST SERVICE YEAR FINALIZATION
# ============================================================

def test_first_service_year_finalizes_at_anniversary():

    employee = create_employee()

    previous_balance = create_balance(
        balance_id=201,
        entitlement_days="22",
    )

    current_balance = create_balance(
        balance_id=202,
        entitlement_days="0",
    )

    db = MagicMock()

    with (
        patch(
            "app.services.leave_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.leave_service.get_employee_leave_balance_for_update",
            return_value=previous_balance,
        ),
        patch(
            "app.services.leave_service.get_or_create_employee_leave_balance_for_update",
            return_value=current_balance,
        ),
        patch(
            "app.services.leave_service.create_leave_transaction",
        ) as create_transaction,
        patch(
            "app.services.leave_service.record_leave_audit",
        ),
    ):

        result = accrue_annual_leave_for_employee(
            db=db,
            employee_id=10,
            as_of_date=date(2027, 1, 1),
        )

    assert previous_balance.entitlement_days == Decimal("30")

    assert current_balance.entitlement_days == Decimal("0")

    assert (
        result["previous_service_year_finalization"]["additional_credit"]
        == Decimal("8")
    )

    create_transaction.assert_called_once()

    transaction_data = create_transaction.call_args.args[1]

    assert transaction_data["days_delta"] == Decimal("8")
    assert transaction_data["transaction_type"] == "accrual"

    db.commit.assert_called_once()


# ============================================================
# 4. TEST TRANSACTION ROLLBACK
# ============================================================

def test_accrual_rolls_back_when_ledger_creation_fails():

    employee = create_employee()

    balance = create_balance(
        balance_id=101,
        entitlement_days="12",
    )

    db = MagicMock()

    with (
        patch(
            "app.services.leave_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.leave_service.get_or_create_employee_leave_balance_for_update",
            return_value=balance,
        ),
        patch(
            "app.services.leave_service.create_leave_transaction",
            side_effect=RuntimeError("Ledger creation failed"),
        ),
        patch(
            "app.services.leave_service.record_leave_audit",
        ),
    ):

        with pytest.raises(
            RuntimeError,
            match="Ledger creation failed",
        ):
            accrue_annual_leave_for_employee(
                db=db,
                employee_id=10,
                as_of_date=date(2026, 8, 1),
            )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
