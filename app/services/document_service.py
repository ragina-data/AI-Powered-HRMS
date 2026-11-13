
"""
HR Document Service
===================

Purpose:
    Implement business logic for HR Document Management.

Responsibilities:
    1. Validate employee eligibility.
    2. Validate document types.
    3. Submit document requests.
    4. Retrieve employee document requests.
    5. Retrieve requests for HR processing.
    6. Enforce valid document status transitions.
    7. Record document request history.

Transaction management:
    Database commits and rollbacks are handled here.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User

from app.repositories.employee_repository import (
    get_employee_by_id,
)

from app.repositories.document_repository import (
    get_active_document_types,
    get_document_type_by_code,
    create_document_request,
    get_employee_document_requests,
    get_document_requests,
    get_document_request_by_id,
    create_document_request_history,
    get_document_request_history,
)


# ============================================================
# DOCUMENT STATUS CONFIGURATION
# ============================================================

DOCUMENT_STATUSES = {
    "pending",
    "approved",
    "processing",
    "completed",
    "rejected",
    "cancelled",
}


DOCUMENT_STATUS_TRANSITIONS = {
    "pending": {"approved", "rejected", "cancelled"},
    "approved": {"processing", "rejected", "cancelled"},
    "processing": {"completed", "rejected", "cancelled"},
    "completed": set(),
    "rejected": set(),
    "cancelled": set(),
}


# ============================================================
# 1. RETRIEVE ACTIVE DOCUMENT TYPES
# ============================================================

def list_active_document_types(
    db: Session,
):
    """
    Retrieve document types currently available to employees.
    """

    return get_active_document_types(db)


# ============================================================
# 2. SUBMIT DOCUMENT REQUEST
# ============================================================

def submit_document_request(
    db: Session,
    current_user: User,
    request_data: dict,
):
    """
    Submit a new HR document request for the authenticated
    employee.

    Initial status:
        pending

    An initial history record is created in the same
    database transaction.
    """

    try:

        # Verify employee account linkage.

        if current_user.employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not linked to an employee profile",
            )

        employee = get_employee_by_id(
            db,
            current_user.employee_id,
        )

        if employee is None or not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee profile is unavailable or inactive",
            )

        # Validate the requested document type.

        document_type_code = (
            request_data["document_type"]
            .strip()
            .lower()
        )

        document_type = get_document_type_by_code(
            db,
            document_type_code,
        )

        if document_type is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive document type",
            )

        # Create document request.

        document_request = create_document_request(
            db,
            {
                "employee_id": employee.employee_id,
                "document_type": document_type_code,
                "purpose": request_data.get("purpose"),
                "status": "pending",
            },
        )

        # Record initial history.

        create_document_request_history(
            db,
            {
                "document_request_id": (
                    document_request.document_request_id
                ),
                "previous_status": None,
                "new_status": "pending",
                "action_by_user_id": current_user.user_id,
                "comments": "Document request submitted",
            },
        )

        db.commit()
        db.refresh(document_request)

        return document_request

    except Exception:
        db.rollback()
        raise


# ============================================================
# 3. RETRIEVE EMPLOYEE DOCUMENT REQUESTS
# ============================================================

def get_my_document_requests(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
):
    """
    Retrieve document requests belonging to the
    authenticated employee only.
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to an employee profile",
        )

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    return get_employee_document_requests(
        db=db,
        employee_id=current_user.employee_id,
        skip=skip,
        limit=limit,
    )


# ============================================================
# 4. RETRIEVE DOCUMENT REQUESTS FOR HR
# ============================================================

def list_document_requests(
    db: Session,
    request_status: str | None = None,
    employee_id: int | None = None,
    document_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
):
    """
    Retrieve document requests for authorized HR users.

    Authorization is enforced by the API permission layer.
    """

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    if (
        request_status is not None
        and request_status not in DOCUMENT_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document request status",
        )

    return get_document_requests(
        db=db,
        request_status=request_status,
        employee_id=employee_id,
        document_type=document_type,
        skip=skip,
        limit=limit,
    )


# ============================================================
# 5. PROCESS DOCUMENT REQUEST
# ============================================================

def process_document_request(
    db: Session,
    document_request_id: int,
    processing_data: dict,
    current_user: User,
):
    """
    Process an employee document request.

    Supported transitions:

        pending -> approved
        pending -> rejected

        approved -> processing
        approved -> rejected

        processing -> completed
        processing -> rejected

    The service also records every successful status change
    in HRDocumentRequestHistory.

    The request update and history record are committed
    together as one database transaction.
    """

    try:

        # Retrieve request with a database row lock.

        document_request = get_document_request_by_id(
            db=db,
            document_request_id=document_request_id,
            for_update=True,
        )

        if document_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document request not found",
            )

        requested_status = processing_data["status"]

        if requested_status not in DOCUMENT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document status",
            )

        current_status = document_request.status

        allowed_transitions = DOCUMENT_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )

        if requested_status not in allowed_transitions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid document status transition: "
                    f"{current_status} -> {requested_status}"
                ),
            )

        # Update request status and processing metadata.

        document_request.status = requested_status

        document_request.processed_by_employee_id = (
            current_user.employee_id
        )

        document_request.processed_at = datetime.now(
            timezone.utc
        )

        document_request.remarks = processing_data.get(
            "remarks"
        )

        document_reference = processing_data.get(
            "document_reference"
        )

        if document_reference is not None:
            document_request.document_reference = (
                document_reference
            )

        # Create request history.

        create_document_request_history(
            db,
            {
                "document_request_id": (
                    document_request.document_request_id
                ),
                "previous_status": current_status,
                "new_status": requested_status,
                "action_by_user_id": current_user.user_id,
                "comments": processing_data.get("remarks"),
            },
        )

        db.commit()
        db.refresh(document_request)

        return document_request

    except Exception:
        db.rollback()
        raise


# ============================================================
# 6. RETRIEVE EMPLOYEE DOCUMENT REQUEST HISTORY
# ============================================================

def get_my_document_request_history(
    db: Session,
    current_user: User,
    document_request_id: int,
):
    """
    Retrieve history belonging to the authenticated
    employee's own document request.
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to an employee profile",
        )

    document_request = get_document_request_by_id(
        db=db,
        document_request_id=document_request_id,
    )

    if (
        document_request is None
        or document_request.employee_id != current_user.employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document request not found",
        )

    return get_document_request_history(
        db=db,
        document_request_id=document_request_id,
    )
