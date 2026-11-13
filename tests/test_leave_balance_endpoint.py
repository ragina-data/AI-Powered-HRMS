
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db


# ============================================================
# MOCK DATABASE PERMISSION QUERY
# ============================================================

class MockPermissionQuery:

    def __init__(self, permissions):
        self.permissions = permissions

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def all(self):
        return [(permission,) for permission in self.permissions]


class MockDB:

    def __init__(self, permissions):
        self.permissions = permissions

    def query(self, *args, **kwargs):
        return MockPermissionQuery(self.permissions)


# ============================================================
# TEST HELPERS
# ============================================================

@contextmanager
def authenticated_client(
    role_name,
    permission_codes,
    employee_id=None,
):

    original_overrides = app.dependency_overrides.copy()

    user = SimpleNamespace(
        user_id=1,
        employee_id=employee_id,
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(
                    role_name=role_name
                )
            )
        ],
    )

    db = MockDB(permission_codes)

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    app.dependency_overrides[get_db] = (
        lambda: db
    )

    try:
        with TestClient(app) as client:
            yield client, user, db

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(
            original_overrides
        )


# ============================================================
# 1. EMPLOYEE CANNOT ACCESS ORGANIZATION BALANCES
# ============================================================

def test_employee_cannot_access_organization_balances():

    with authenticated_client(
        role_name="employee",
        permission_codes=["leave.read_self"],
        employee_id=10,
    ) as (client, user, db):

        with patch(
            "app.api.leaves.get_leave_balances_for_user"
        ) as service:

            response = client.get(
                "/api/v1/leaves/balances"
            )

    assert response.status_code == 403
    service.assert_not_called()


# ============================================================
# 2. MANAGER CAN ACCESS AUTHORIZED BALANCES
# ============================================================

def test_manager_can_access_authorized_balances():

    with authenticated_client(
        role_name="manager",
        permission_codes=["employee.read_team"],
        employee_id=10,
    ) as (client, user, db):

        with patch(
            "app.api.leaves.get_leave_balances_for_user",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/leaves/balances",
                params={
                    "balance_year": 2026,
                    "skip": 0,
                    "limit": 100,
                },
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(
        db=db,
        current_user=user,
        employee_id=None,
        balance_year=2026,
        skip=0,
        limit=100,
    )


# ============================================================
# 3. HR CAN ACCESS ORGANIZATION BALANCES
# ============================================================

def test_hr_can_access_organization_balances():

    with authenticated_client(
        role_name="hr",
        permission_codes=["leave.manage_all"],
    ) as (client, user, db):

        with patch(
            "app.api.leaves.get_leave_balances_for_user",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/leaves/balances"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once()


# ============================================================
# 4. ADMIN CAN ACCESS ORGANIZATION BALANCES
# ============================================================

def test_admin_can_access_organization_balances():

    with authenticated_client(
        role_name="admin",
        permission_codes=["leave.manage_all"],
    ) as (client, user, db):

        with patch(
            "app.api.leaves.get_leave_balances_for_user",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/leaves/balances"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once()


# ============================================================
# 5. USER WITHOUT PERMISSION IS REJECTED
# ============================================================

def test_user_without_balance_permission_is_rejected():

    with authenticated_client(
        role_name="employee",
        permission_codes=[],
        employee_id=10,
    ) as (client, user, db):

        with patch(
            "app.api.leaves.get_leave_balances_for_user"
        ) as service:

            response = client.get(
                "/api/v1/leaves/balances"
            )

    assert response.status_code == 403
    service.assert_not_called()
