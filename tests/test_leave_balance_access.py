
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.leave_service import get_leave_balances_for_user


# ============================================================
# TEST HELPERS
# ============================================================

def create_user(
    role_name: str,
    employee_id: int | None = None,
):
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
# 1. EMPLOYEE CAN ACCESS OWN BALANCES
# ============================================================

def test_employee_can_access_own_balances():

    db = MagicMock()
    user = create_user("employee", employee_id=10)

    employees = [
        SimpleNamespace(employee_id=10)
    ]

    balances = [MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 1),
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_balances_for_employees",
            return_value=balances,
        ) as get_balances,
    ):

        result = get_leave_balances_for_user(
            db=db,
            current_user=user,
            balance_year=2026,
        )

    assert result == balances

    get_employees.assert_called_once_with(
        db=db,
        employee_id=10,
        reporting_scope_manager_id=None,
        skip=0,
        limit=100,
    )

    get_balances.assert_called_once_with(
        db=db,
        employee_ids=[10],
        balance_year=2026,
    )


# ============================================================
# 2. EMPLOYEE CANNOT ACCESS ANOTHER EMPLOYEE
# ============================================================

def test_employee_cannot_access_another_employee_balances():

    db = MagicMock()
    user = create_user("employee", employee_id=10)

    with (
        patch(
            "app.services.leave_service.get_employees"
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_balances_for_employees"
        ) as get_balances,
    ):

        result = get_leave_balances_for_user(
            db=db,
            current_user=user,
            employee_id=20,
        )

    assert result == []

    get_employees.assert_not_called()
    get_balances.assert_not_called()


# ============================================================
# 3. MANAGER CAN ACCESS OWN AND DIRECT REPORT BALANCES
# ============================================================

def test_manager_can_access_authorized_team_balances():

    db = MagicMock()
    user = create_user("manager", employee_id=10)

    employees = [
        SimpleNamespace(employee_id=10),
        SimpleNamespace(employee_id=11),
        SimpleNamespace(employee_id=12),
    ]

    balances = [MagicMock(), MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 3),
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_balances_for_employees",
            return_value=balances,
        ) as get_balances,
    ):

        result = get_leave_balances_for_user(
            db=db,
            current_user=user,
        )

    assert result == balances

    get_employees.assert_called_once_with(
        db=db,
        employee_id=None,
        reporting_scope_manager_id=10,
        skip=0,
        limit=100,
    )

    get_balances.assert_called_once_with(
        db=db,
        employee_ids=[10, 11, 12],
        balance_year=None,
    )


# ============================================================
# 4. MANAGER CANNOT ACCESS EMPLOYEE OUTSIDE TEAM
# ============================================================

def test_manager_cannot_access_employee_outside_reporting_scope():

    db = MagicMock()
    user = create_user("manager", employee_id=10)

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=([], 0),
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_balances_for_employees",
            return_value=[],
        ) as get_balances,
    ):

        result = get_leave_balances_for_user(
            db=db,
            current_user=user,
            employee_id=99,
        )

    assert result == []

    get_employees.assert_called_once_with(
        db=db,
        employee_id=99,
        reporting_scope_manager_id=10,
        skip=0,
        limit=100,
    )

    get_balances.assert_called_once_with(
        db=db,
        employee_ids=[],
        balance_year=None,
    )


# ============================================================
# 5. HR AND ADMIN CAN ACCESS ORGANIZATION BALANCES
# ============================================================

@pytest.mark.parametrize(
    "role_name",
    ["hr", "admin"],
)
def test_hr_and_admin_can_access_all_employee_balances(
    role_name,
):

    db = MagicMock()
    user = create_user(role_name)

    employees = [
        SimpleNamespace(employee_id=10),
        SimpleNamespace(employee_id=11),
        SimpleNamespace(employee_id=12),
    ]

    balances = [MagicMock(), MagicMock(), MagicMock()]

    with (
        patch(
            "app.services.leave_service.get_employees",
            return_value=(employees, 3),
        ) as get_employees,
        patch(
            "app.services.leave_service.get_leave_balances_for_employees",
            return_value=balances,
        ) as get_balances,
    ):

        result = get_leave_balances_for_user(
            db=db,
            current_user=user,
            balance_year=2026,
        )

    assert result == balances

    get_employees.assert_called_once_with(
        db=db,
        employee_id=None,
        reporting_scope_manager_id=None,
        skip=0,
        limit=100,
    )

    get_balances.assert_called_once_with(
        db=db,
        employee_ids=[10, 11, 12],
        balance_year=2026,
    )


# ============================================================
# 6. INVALID PAGINATION IS REJECTED
# ============================================================

def test_invalid_pagination_is_rejected():

    db = MagicMock()
    user = create_user("admin")

    with pytest.raises(Exception):
        get_leave_balances_for_user(
            db=db,
            current_user=user,
            skip=-1,
        )
