
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.leave_service import (
    get_leave_transactions_for_user,
)


def create_user(role_name, employee_id=None):
    return SimpleNamespace(
        user_id=1,
        employee_id=employee_id,
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(role_name=role_name)
            )
        ],
    )


# ============================================================
# 1. EMPLOYEE CAN RETRIEVE OWN TRANSACTIONS
# ============================================================

def test_employee_can_retrieve_own_transactions():

    db = MagicMock()
    user = create_user("employee", 10)

    employees = [SimpleNamespace(employee_id=10)]
    transactions = [MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 1),
        ),
        patch(
            "app.services.leave_service.get_leave_transactions_for_employees",
            return_value=transactions,
        ) as get_transactions,
    ):

        result = get_leave_transactions_for_user(
            db=db,
            current_user=user,
            transaction_type="accrual",
            leave_type="annual",
            balance_year=2026,
        )

    assert result == transactions

    get_transactions.assert_called_once_with(
        db=db,
        employee_ids=[10],
        transaction_type="accrual",
        leave_type="annual",
        balance_year=2026,
        skip=0,
        limit=100,
    )


# ============================================================
# 2. EMPLOYEE CANNOT ACCESS ANOTHER EMPLOYEE
# ============================================================

def test_employee_cannot_access_another_employee_transactions():

    db = MagicMock()
    user = create_user("employee", 10)

    with (
        patch(
            "app.services.leave_service.get_employees"
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_transactions_for_employees"
        ) as get_transactions,
    ):

        result = get_leave_transactions_for_user(
            db=db,
            current_user=user,
            employee_id=20,
        )

    assert result == []

    get_employees.assert_not_called()
    get_transactions.assert_not_called()


# ============================================================
# 3. MANAGER CAN ACCESS AUTHORIZED TEAM TRANSACTIONS
# ============================================================

def test_manager_can_access_authorized_team_transactions():

    db = MagicMock()
    user = create_user("manager", 10)

    employees = [
        SimpleNamespace(employee_id=10),
        SimpleNamespace(employee_id=11),
        SimpleNamespace(employee_id=12),
    ]

    transactions = [MagicMock(), MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 3),
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_transactions_for_employees",
            return_value=transactions,
        ) as get_transactions,
    ):

        result = get_leave_transactions_for_user(
            db=db,
            current_user=user,
            balance_year=2026,
        )

    assert result == transactions

    get_employees.assert_called_once_with(
        db=db,
        employee_id=None,
        reporting_scope_manager_id=10,
        skip=0,
        limit=500,
    )

    get_transactions.assert_called_once_with(
        db=db,
        employee_ids=[10, 11, 12],
        transaction_type=None,
        leave_type=None,
        balance_year=2026,
        skip=0,
        limit=100,
    )


# ============================================================
# 4. MANAGER CANNOT ACCESS EMPLOYEES OUTSIDE THEIR TEAM
# ============================================================

def test_manager_cannot_access_outside_team_transactions():

    db = MagicMock()
    user = create_user("manager", 10)

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=([], 0),
        ),
        patch(
            "app.services.leave_service.get_leave_transactions_for_employees",
            return_value=[],
        ) as get_transactions,
    ):

        result = get_leave_transactions_for_user(
            db=db,
            current_user=user,
            employee_id=99,
        )

    assert result == []

    get_transactions.assert_called_once_with(
        db=db,
        employee_ids=[],
        transaction_type=None,
        leave_type=None,
        balance_year=None,
        skip=0,
        limit=100,
    )


# ============================================================
# 5. HR AND ADMIN CAN ACCESS ORGANIZATION TRANSACTIONS
# ============================================================

@pytest.mark.parametrize("role_name", ["hr", "admin"])
def test_hr_and_admin_can_access_all_transactions(role_name):

    db = MagicMock()
    user = create_user(role_name)

    employees = [
        SimpleNamespace(employee_id=10),
        SimpleNamespace(employee_id=11),
    ]

    transactions = [MagicMock(), MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 2),
        ),
        patch(
            "app.services.leave_service.get_leave_transactions_for_employees",
            return_value=transactions,
        ) as get_transactions,
    ):

        result = get_leave_transactions_for_user(
            db=db,
            current_user=user,
        )

    assert result == transactions

    get_transactions.assert_called_once_with(
        db=db,
        employee_ids=[10, 11],
        transaction_type=None,
        leave_type=None,
        balance_year=None,
        skip=0,
        limit=100,
    )


# ============================================================
# 6. INVALID PAGINATION IS REJECTED
# ============================================================

def test_transaction_history_rejects_invalid_pagination():

    db = MagicMock()
    user = create_user("admin")

    with pytest.raises(Exception):

        get_leave_transactions_for_user(
            db=db,
            current_user=user,
            skip=-1,
        )
