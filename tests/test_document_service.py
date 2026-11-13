
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.document_service import (
    submit_document_request,
    get_my_document_requests,
    list_document_requests,
    process_document_request,
    get_my_document_request_history,
)


def create_user(employee_id=10, user_id=5):
    return SimpleNamespace(
        user_id=user_id,
        employee_id=employee_id,
    )


# ============================================================
# 1. SUCCESSFUL DOCUMENT REQUEST SUBMISSION
# ============================================================

def test_submit_document_request_success():

    db = MagicMock()
    user = create_user()

    employee = SimpleNamespace(
        employee_id=10,
        is_active=True,
    )

    document_type = SimpleNamespace(
        document_type_code="employment_certificate",
    )

    document_request = SimpleNamespace(
        document_request_id=100,
        employee_id=10,
        status="pending",
    )

    request_data = {
        "document_type": " employment_certificate ",
        "purpose": "Bank application",
    }

    with (
        patch(
            "app.services.document_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.document_service.get_document_type_by_code",
            return_value=document_type,
        ),
        patch(
            "app.services.document_service.create_document_request",
            return_value=document_request,
        ) as create_request,
        patch(
            "app.services.document_service.create_document_request_history",
        ) as create_history,
    ):

        result = submit_document_request(
            db,
            user,
            request_data,
        )

    assert result is document_request
    assert result.status == "pending"

    create_request.assert_called_once_with(
        db,
        {
            "employee_id": 10,
            "document_type": "employment_certificate",
            "purpose": "Bank application",
            "status": "pending",
        },
    )

    create_history.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document_request)


# ============================================================
# 2. INACTIVE EMPLOYEE CANNOT SUBMIT
# ============================================================

def test_inactive_employee_cannot_submit_document_request():

    db = MagicMock()
    user = create_user()

    employee = SimpleNamespace(
        employee_id=10,
        is_active=False,
    )

    with patch(
        "app.services.document_service.get_employee_by_id",
        return_value=employee,
    ):

        with pytest.raises(HTTPException) as exc_info:
            submit_document_request(
                db,
                user,
                {"document_type": "employment_certificate"},
            )

    assert exc_info.value.status_code == 403
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


# ============================================================
# 3. INVALID DOCUMENT TYPE IS REJECTED
# ============================================================

def test_invalid_document_type_is_rejected():

    db = MagicMock()
    user = create_user()

    employee = SimpleNamespace(
        employee_id=10,
        is_active=True,
    )

    with (
        patch(
            "app.services.document_service.get_employee_by_id",
            return_value=employee,
        ),
        patch(
            "app.services.document_service.get_document_type_by_code",
            return_value=None,
        ),
    ):

        with pytest.raises(HTTPException) as exc_info:
            submit_document_request(
                db,
                user,
                {"document_type": "invalid_document"},
            )

    assert exc_info.value.status_code == 400
    db.rollback.assert_called_once()


# ============================================================
# 4. EMPLOYEE CAN RETRIEVE OWN REQUESTS
# ============================================================

def test_employee_can_retrieve_own_document_requests():

    db = MagicMock()
    user = create_user()

    requests = [MagicMock(), MagicMock()]

    with patch(
        "app.services.document_service.get_employee_document_requests",
        return_value=requests,
    ) as repository:

        result = get_my_document_requests(
            db,
            user,
            skip=0,
            limit=20,
        )

    assert result == requests

    repository.assert_called_once_with(
        db=db,
        employee_id=10,
        skip=0,
        limit=20,
    )


# ============================================================
# 5. INVALID DOCUMENT REQUEST PAGINATION IS REJECTED
# ============================================================

def test_document_request_invalid_pagination():

    db = MagicMock()
    user = create_user()

    with pytest.raises(HTTPException) as exc_info:

        get_my_document_requests(
            db,
            user,
            skip=-1,
        )

    assert exc_info.value.status_code == 400


# ============================================================
# 6. INVALID HR REQUEST STATUS IS REJECTED
# ============================================================

def test_invalid_hr_document_status_is_rejected():

    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:

        list_document_requests(
            db,
            request_status="invalid_status",
        )

    assert exc_info.value.status_code == 400


# ============================================================
# 7. HR CAN APPROVE A PENDING REQUEST
# ============================================================

def test_hr_can_approve_pending_document_request():

    db = MagicMock()
    user = create_user(employee_id=20, user_id=7)

    document_request = SimpleNamespace(
        document_request_id=100,
        employee_id=10,
        status="pending",
        processed_by_employee_id=None,
        processed_at=None,
        remarks=None,
        document_reference=None,
    )

    with (
        patch(
            "app.services.document_service.get_document_request_by_id",
            return_value=document_request,
        ) as get_request,
        patch(
            "app.services.document_service.create_document_request_history",
        ) as create_history,
    ):

        result = process_document_request(
            db=db,
            document_request_id=100,
            processing_data={
                "status": "approved",
                "remarks": "Approved by HR",
            },
            current_user=user,
        )

    assert result.status == "approved"
    assert result.processed_by_employee_id == 20
    assert result.processed_at is not None
    assert isinstance(result.processed_at, datetime)
    assert result.remarks == "Approved by HR"

    get_request.assert_called_once_with(
        db=db,
        document_request_id=100,
        for_update=True,
    )

    create_history.assert_called_once()

    history_data = create_history.call_args.args[1]

    assert history_data["previous_status"] == "pending"
    assert history_data["new_status"] == "approved"
    assert history_data["action_by_user_id"] == 7

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document_request)


# ============================================================
# 8. INVALID STATUS TRANSITION IS REJECTED
# ============================================================

def test_completed_request_cannot_be_approved_again():

    db = MagicMock()
    user = create_user()

    document_request = SimpleNamespace(
        document_request_id=100,
        employee_id=10,
        status="completed",
    )

    with (
        patch(
            "app.services.document_service.get_document_request_by_id",
            return_value=document_request,
        ),
        patch(
            "app.services.document_service.create_document_request_history",
        ) as create_history,
    ):

        with pytest.raises(HTTPException) as exc_info:

            process_document_request(
                db=db,
                document_request_id=100,
                processing_data={"status": "approved"},
                current_user=user,
            )

    assert exc_info.value.status_code == 400
    create_history.assert_not_called()
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


# ============================================================
# 9. EMPLOYEE CANNOT ACCESS ANOTHER EMPLOYEE'S HISTORY
# ============================================================

def test_employee_cannot_access_another_employee_history():

    db = MagicMock()
    user = create_user(employee_id=10)

    document_request = SimpleNamespace(
        document_request_id=100,
        employee_id=99,
    )

    with (
        patch(
            "app.services.document_service.get_document_request_by_id",
            return_value=document_request,
        ),
        patch(
            "app.services.document_service.get_document_request_history",
        ) as get_history,
    ):

        with pytest.raises(HTTPException) as exc_info:

            get_my_document_request_history(
                db=db,
                current_user=user,
                document_request_id=100,
            )

    assert exc_info.value.status_code == 404
    get_history.assert_not_called()
