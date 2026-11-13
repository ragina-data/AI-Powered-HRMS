
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.db.session import get_db


# ============================================================
# MOCK PERMISSION QUERY
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
    permissions,
    employee_id=10,
):

    original_overrides = app.dependency_overrides.copy()

    user = SimpleNamespace(
        user_id=1,
        employee_id=employee_id,
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(role_name=role_name)
            )
        ],
    )

    db = MockDB(permissions)

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


def create_document_request_response():

    return SimpleNamespace(
        document_request_id=100,
        employee_id=10,
        document_type="employment_certificate",
        purpose="Bank application",
        status="pending",
        requested_at=datetime.now(timezone.utc),
        processed_by_employee_id=None,
        processed_at=None,
        remarks=None,
        document_reference=None,
    )


# ============================================================
# 1. EMPLOYEE CAN RETRIEVE DOCUMENT TYPES
# ============================================================

def test_employee_can_retrieve_document_types():

    with authenticated_client(
        "employee",
        ["document.request"],
    ) as (client, user, db):

        with patch(
            "app.api.documents.list_active_document_types",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/documents/types"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(db)


# ============================================================
# 2. EMPLOYEE CAN SUBMIT DOCUMENT REQUEST
# ============================================================

def test_employee_can_submit_document_request():

    document_request = create_document_request_response()

    with authenticated_client(
        "employee",
        ["document.request"],
    ) as (client, user, db):

        with patch(
            "app.api.documents.submit_document_request",
            return_value=document_request,
        ) as service:

            response = client.post(
                "/api/v1/documents/requests",
                json={
                    "document_type": "employment_certificate",
                    "purpose": "Bank application",
                },
            )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["employee_id"] == 10

    service.assert_called_once_with(
        db=db,
        current_user=user,
        request_data={
            "document_type": "employment_certificate",
            "purpose": "Bank application",
        },
    )


# ============================================================
# 3. EMPLOYEE CAN RETRIEVE OWN REQUESTS
# ============================================================

def test_employee_can_retrieve_own_requests():

    with authenticated_client(
        "employee",
        ["document.read_self"],
    ) as (client, user, db):

        with patch(
            "app.api.documents.get_my_document_requests",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/documents/requests/me"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(
        db=db,
        current_user=user,
        skip=0,
        limit=20,
    )


# ============================================================
# 4. EMPLOYEE CANNOT ACCESS HR REQUEST LIST
# ============================================================

def test_employee_cannot_access_hr_document_requests():

    with authenticated_client(
        "employee",
        ["document.request", "document.read_self"],
    ) as (client, user, db):

        with patch(
            "app.api.documents.list_document_requests"
        ) as service:

            response = client.get(
                "/api/v1/documents/requests"
            )

    assert response.status_code == 403
    service.assert_not_called()


# ============================================================
# 5. HR CAN RETRIEVE ORGANIZATION REQUESTS
# ============================================================

def test_hr_can_retrieve_document_requests():

    with authenticated_client(
        "hr",
        ["document.process"],
    ) as (client, user, db):

        with patch(
            "app.api.documents.list_document_requests",
            return_value=[],
        ) as service:

            response = client.get(
                "/api/v1/documents/requests",
                params={
                    "request_status": "pending",
                    "skip": 0,
                    "limit": 20,
                },
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(
        db=db,
        request_status="pending",
        employee_id=None,
        document_type=None,
        skip=0,
        limit=20,
    )


# ============================================================
# 6. HR CAN APPROVE DOCUMENT REQUEST
# ============================================================

def test_hr_can_approve_document_request():

    document_request = create_document_request_response()
    document_request.status = "approved"

    with authenticated_client(
        "hr",
        ["document.process"],
        employee_id=20,
    ) as (client, user, db):

        with patch(
            "app.api.documents.process_document_request",
            return_value=document_request,
        ) as service:

            response = client.patch(
                "/api/v1/documents/requests/100/process",
                json={
                    "status": "approved",
                    "remarks": "Approved by HR",
                },
            )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    service.assert_called_once_with(
        db=db,
        document_request_id=100,
        processing_data={
            "status": "approved",
            "remarks": "Approved by HR",
            "document_reference": None,
        },
        current_user=user,
    )


# ============================================================
# 7. EMPLOYEE CAN RETRIEVE OWN REQUEST HISTORY
# ============================================================

def test_employee_can_retrieve_own_request_history():

    with authenticated_client(
        "employee",
        ["document.read_self"],
    ) as (client, user, db):

        with (
            patch(
                "app.api.documents.user_has_permission",
                return_value=False,
            ),
            patch(
                "app.api.documents.get_my_document_request_history",
                return_value=[],
            ) as service,
        ):

            response = client.get(
                "/api/v1/documents/requests/100/history"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(
        db=db,
        current_user=user,
        document_request_id=100,
    )


# ============================================================
# 8. HR CAN RETRIEVE ORGANIZATION REQUEST HISTORY
# ============================================================

def test_hr_can_retrieve_any_document_request_history():

    document_request = SimpleNamespace(
        document_request_id=100,
        employee_id=99,
    )

    with authenticated_client(
        "hr",
        ["document.process"],
        employee_id=20,
    ) as (client, user, db):

        with (
            patch(
                "app.api.documents.user_has_permission",
                return_value=True,
            ),
            patch(
                "app.api.documents.get_document_request_by_id",
                return_value=document_request,
            ),
            patch(
                "app.api.documents.get_document_request_history",
                return_value=[],
            ) as service,
        ):

            response = client.get(
                "/api/v1/documents/requests/100/history"
            )

    assert response.status_code == 200
    assert response.json() == []

    service.assert_called_once_with(
        db=db,
        document_request_id=100,
    )
