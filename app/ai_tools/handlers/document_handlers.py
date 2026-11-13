
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User

from app.services.document_service import (
    list_active_document_types,
    submit_document_request,
    get_my_document_requests as service_get_my_document_requests,
    list_document_requests,
    process_document_request,
    get_my_document_request_history as service_get_my_document_request_history,
)

from app.repositories.document_repository import (
    get_document_request_by_id,
    get_document_request_history,
)


# ============================================================
# SERIALIZERS
# ============================================================

def serialize_document_type(document_type) -> dict:
    return {
        "document_type_id": document_type.document_type_id,
        "document_type_code": document_type.document_type_code,
        "document_type_name": document_type.document_type_name,
        "description": document_type.description,
        "requires_hr_approval": document_type.requires_hr_approval,
        "is_active": document_type.is_active,
    }


def serialize_document_request(document_request) -> dict:
    return {
        "document_request_id": document_request.document_request_id,
        "employee_id": document_request.employee_id,
        "document_type": document_request.document_type,
        "purpose": document_request.purpose,
        "status": document_request.status,
        "requested_at": (
            document_request.requested_at.isoformat()
            if document_request.requested_at else None
        ),
        "processed_by_employee_id": (
            document_request.processed_by_employee_id
        ),
        "processed_at": (
            document_request.processed_at.isoformat()
            if document_request.processed_at else None
        ),
        "remarks": document_request.remarks,
        "document_reference": document_request.document_reference,
    }


def serialize_document_history(history) -> dict:
    return {
        "history_id": history.history_id,
        "document_request_id": history.document_request_id,
        "previous_status": history.previous_status,
        "new_status": history.new_status,
        "action_by_user_id": history.action_by_user_id,
        "comments": history.comments,
        "action_at": (
            history.action_at.isoformat()
            if history.action_at else None
        ),
    }


# ============================================================
# 1. LIST AVAILABLE DOCUMENT TYPES
# ============================================================

def list_available_document_types(
    db: Session,
    current_user: User,
) -> list[dict]:

    document_types = list_active_document_types(db)

    return [
        serialize_document_type(item)
        for item in document_types
    ]


# ============================================================
# 2. SUBMIT DOCUMENT REQUEST
# ============================================================

def submit_document_request_handler(
    db: Session,
    current_user: User,
    document_type: str,
    purpose: str | None = None,
) -> dict:

    document_request = submit_document_request(
        db=db,
        current_user=current_user,
        request_data={
            "document_type": document_type,
            "purpose": purpose,
        },
    )

    return serialize_document_request(document_request)


# ============================================================
# 3. RETRIEVE MY DOCUMENT REQUESTS
# ============================================================

def get_my_document_requests(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[dict]:

    requests = service_get_my_document_requests(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_document_request(item)
        for item in requests
    ]


# ============================================================
# 4. RETRIEVE AUTHORIZED DOCUMENT REQUESTS
# ============================================================

def get_authorized_document_requests(
    db: Session,
    current_user: User,
    request_status: str | None = None,
    employee_id: int | None = None,
    document_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[dict]:

    # Permission enforcement is performed by the tool executor.

    requests = list_document_requests(
        db=db,
        request_status=request_status,
        employee_id=employee_id,
        document_type=document_type,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_document_request(item)
        for item in requests
    ]


# ============================================================
# 5. PROCESS DOCUMENT REQUEST
# ============================================================

def process_document_request_handler(
    db: Session,
    current_user: User,
    document_request_id: int,
    status: str,
    remarks: str | None = None,
    document_reference: str | None = None,
) -> dict:

    document_request = process_document_request(
        db=db,
        document_request_id=document_request_id,
        processing_data={
            "status": status,
            "remarks": remarks,
            "document_reference": document_reference,
        },
        current_user=current_user,
    )

    return serialize_document_request(document_request)


# ============================================================
# 6. RETRIEVE MY DOCUMENT REQUEST HISTORY
# ============================================================

def get_my_document_request_history(
    db: Session,
    current_user: User,
    document_request_id: int,
) -> list[dict]:

    history = service_get_my_document_request_history(
        db=db,
        current_user=current_user,
        document_request_id=document_request_id,
    )

    return [
        serialize_document_history(item)
        for item in history
    ]


# ============================================================
# 7. RETRIEVE AUTHORIZED DOCUMENT REQUEST HISTORY
# ============================================================

def get_authorized_document_request_history(
    db: Session,
    current_user: User,
    document_request_id: int,
) -> list[dict]:

    # Permission enforcement is performed by the tool executor.

    document_request = get_document_request_by_id(
        db=db,
        document_request_id=document_request_id,
    )

    if document_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document request not found",
        )

    history = get_document_request_history(
        db=db,
        document_request_id=document_request_id,
    )

    return [
        serialize_document_history(item)
        for item in history
    ]
