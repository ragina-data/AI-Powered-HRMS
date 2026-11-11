import pytest
from fastapi import HTTPException

from app.api.permissions import require_role, require_permission
from app.models.user import User



from types import SimpleNamespace

def test_require_role_accepts_authorized_user():
    user = SimpleNamespace(
        user_id=1,
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(role_name="admin")
            )
        ]
    )

    authorized_user = require_role("admin")(user)

    assert authorized_user is user

def test_require_role_rejects_unauthorized_user():
    user = User(user_id=1)

    with pytest.raises(HTTPException) as exc_info:
        require_role("admin")(user)

    assert exc_info.value.status_code == 403


def test_require_permission_accepts_authorized_user():
    user = User(user_id=1)

    class MockQuery:
        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def distinct(self):
            return self

        def all(self):
            return [("employee.read_self",)]

    class MockDB:
        def query(self, *args, **kwargs):
            return MockQuery()

    authorized_user = require_permission("employee.read_self")(
        user, MockDB()
    )

    assert authorized_user is user


def test_require_permission_rejects_unauthorized_user():
    user = User(user_id=1)

    class MockQuery:
        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def distinct(self):
            return self

        def all(self):
            return []

    class MockDB:
        def query(self, *args, **kwargs):
            return MockQuery()

    with pytest.raises(HTTPException) as exc_info:
        require_permission("employee.read_self")(user, MockDB())

    assert exc_info.value.status_code == 403