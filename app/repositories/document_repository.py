
"""
HR Document Repository
======================

Purpose:
    Handle database operations for HR Document Management.

Responsibilities:
    1. Retrieve active document types.
    2. Create document requests.
    3. Retrieve employee document requests.
    4. Retrieve requests for HR processing.
    5. Retrieve individual requests with optional row locking.
    6. Record request history.
    7. Retrieve request history.

Transaction management:
    Database commits and rollbacks are handled by
    the service layer.

Security:
    Authorization and employee visibility are enforced
    by the service layer before repository access.
"""

from sqlalchemy.orm import Session

from app.models.hr_document_request import HRDocumentRequest
from app.models.hr_document_request_history import (
    HRDocumentRequestHistory,
)
from app.models.hr_document_type import HRDocumentType


# ============================================================
# 1. DOCUMENT TYPE CATALOGUE
# ============================================================

def get_active_document_types(
    db: Session,
) -> list[HRDocumentType]:
    """
    Retrieve all active HR document types.
    """

    return (
        db.query(HRDocumentType)
        .filter(
            HRDocumentType.is_active.is_(True)
        )
        .order_by(
            HRDocumentType.document_type_name.asc()
        )
        .all()
    )


def get_document_type_by_code(
    db: Session,
    document_type_code: str,
) -> HRDocumentType | None:
    """
    Retrieve one active document type by its code.

    Inactive document types cannot be used for new requests.
    """

    return (
        db.query(HRDocumentType)
        .filter(
            HRDocumentType.document_type_code
            == document_type_code,
            HRDocumentType.is_active.is_(True),
        )
        .first()
    )


# ============================================================
# 2. CREATE DOCUMENT REQUEST
# ============================================================

def create_document_request(
    db: Session,
    request_data: dict,
) -> HRDocumentRequest:
    """
    Create a new HR document request.

    The service layer is responsible for committing.
    """

    document_request = HRDocumentRequest(
        **request_data
    )

    db.add(document_request)
    db.flush()

    return document_request


# ============================================================
# 3. RETRIEVE EMPLOYEE DOCUMENT REQUESTS
# ============================================================

def get_employee_document_requests(
    db: Session,
    employee_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[HRDocumentRequest]:
    """
    Retrieve document requests belonging to one employee.

    Ordered from newest to oldest.
    """

    return (
        db.query(HRDocumentRequest)
        .filter(
            HRDocumentRequest.employee_id == employee_id
        )
        .order_by(
            HRDocumentRequest.requested_at.desc(),
            HRDocumentRequest.document_request_id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# 4. RETRIEVE DOCUMENT REQUESTS FOR HR
# ============================================================

def get_document_requests(
    db: Session,
    request_status: str | None = None,
    employee_id: int | None = None,
    document_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[HRDocumentRequest]:
    """
    Retrieve document requests for authorized HR processing.

    Optional filters:
        request_status
        employee_id
        document_type
        skip
        limit

    Authorization must be performed by the service layer.
    """

    query = db.query(HRDocumentRequest)

    if request_status is not None:
        query = query.filter(
            HRDocumentRequest.status == request_status
        )

    if employee_id is not None:
        query = query.filter(
            HRDocumentRequest.employee_id == employee_id
        )

    if document_type is not None:
        query = query.filter(
            HRDocumentRequest.document_type == document_type
        )

    return (
        query
        .order_by(
            HRDocumentRequest.requested_at.desc(),
            HRDocumentRequest.document_request_id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# 5. RETRIEVE INDIVIDUAL REQUEST
# ============================================================

def get_document_request_by_id(
    db: Session,
    document_request_id: int,
    for_update: bool = False,
) -> HRDocumentRequest | None:
    """
    Retrieve a document request by its primary key.

    When for_update=True, acquire a database row lock
    for safe concurrent processing.
    """

    query = db.query(HRDocumentRequest).filter(
        HRDocumentRequest.document_request_id
        == document_request_id
    )

    if for_update:
        query = query.with_for_update()

    return query.first()


# ============================================================
# 6. CREATE DOCUMENT REQUEST HISTORY
# ============================================================

def create_document_request_history(
    db: Session,
    history_data: dict,
) -> HRDocumentRequestHistory:
    """
    Record a document request status transition.

    History insertion is part of the caller's transaction.
    """

    history = HRDocumentRequestHistory(
        **history_data
    )

    db.add(history)
    db.flush()

    return history


# ============================================================
# 7. RETRIEVE DOCUMENT REQUEST HISTORY
# ============================================================

def get_document_request_history(
    db: Session,
    document_request_id: int,
) -> list[HRDocumentRequestHistory]:
    """
    Retrieve chronological history for one document request.
    """

    return (
        db.query(HRDocumentRequestHistory)
        .filter(
            HRDocumentRequestHistory.document_request_id
            == document_request_id
        )
        .order_by(
            HRDocumentRequestHistory.action_at.asc(),
            HRDocumentRequestHistory.history_id.asc(),
        )
        .all()
    )
