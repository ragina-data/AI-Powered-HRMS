
"""
HR Document Management API
==========================

Purpose:
    Expose REST API endpoints for HR Document Management.

Responsibilities:
    1. List available document types.
    2. Submit employee document requests.
    3. Retrieve personal document requests.
    4. Retrieve document requests for HR processing.
    5. Approve, reject and complete document requests.
    6. Retrieve document request history.

Security:
    Authentication is required.
    Permissions are enforced through existing RBAC.
    Employees can access only their own requests and history.
    HR and Admin can access organization-wide requests.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.api.permissions import (
    require_permission,
    user_has_permission,
)

from app.db.session import get_db

from app.models.user import User

from app.schemas.document import (
    DocumentTypeResponse,
    DocumentRequestCreate,
    DocumentRequestResponse,
    DocumentProcessRequest,
    DocumentRequestHistoryResponse,
)

from app.repositories.document_repository import (
    get_document_request_by_id,
    get_document_request_history,
)

from app.services.document_service import (
    list_active_document_types,
    submit_document_request,
    get_my_document_requests,
    list_document_requests,
    process_document_request,
    get_my_document_request_history,
)


router = APIRouter(
    prefix="/documents",
    tags=["HR Document Management"],
)


# ============================================================
# 1. GET AVAILABLE DOCUMENT TYPES
# ============================================================

@router.get(
    "/types",
    response_model=list[DocumentTypeResponse],
)
def get_document_types(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("document.request")),
    ],
):
    """
    Retrieve active HR document types.

    Requires:
        document.request
    """

    return list_active_document_types(db)


# ============================================================
# 2. SUBMIT DOCUMENT REQUEST
# ============================================================

@router.post(
    "/requests",
    response_model=DocumentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_request(
    request_data: DocumentRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("document.request")),
    ],
):
    """
    Submit a document request for the authenticated employee.

    Initial status:
        pending

    Requires:
        document.request
    """

    return submit_document_request(
        db=db,
        current_user=current_user,
        request_data=request_data.model_dump(),
    )


# ============================================================
# 3. GET OWN DOCUMENT REQUESTS
# ============================================================

@router.get(
    "/requests/me",
    response_model=list[DocumentRequestResponse],
)
def get_my_document_requests_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("document.read_self")),
    ],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Retrieve document requests belonging to the
    authenticated employee.

    Requires:
        document.read_self
    """

    return get_my_document_requests(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


# ============================================================
# 4. GET DOCUMENT REQUESTS FOR HR
# ============================================================

@router.get(
    "/requests",
    response_model=list[DocumentRequestResponse],
)
def get_all_document_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("document.process")),
    ],
    request_status: Annotated[
        str | None,
        Query(max_length=20),
    ] = None,
    employee_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    document_type: Annotated[
        str | None,
        Query(max_length=50),
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Retrieve document requests for HR/Admin processing.

    Optional filters:
        request_status
        employee_id
        document_type

    Requires:
        document.process
    """

    return list_document_requests(
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

@router.patch(
    "/requests/{document_request_id}/process",
    response_model=DocumentRequestResponse,
)
def process_document_request_endpoint(
    document_request_id: Annotated[int, Path(gt=0)],
    processing_data: DocumentProcessRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("document.process")),
    ],
):
    """
    Process an employee document request.

    Supported transitions include:
        pending -> approved
        pending -> rejected
        approved -> processing
        approved -> rejected
        processing -> completed
        processing -> rejected

    Requires:
        document.process
    """

    return process_document_request(
        db=db,
        document_request_id=document_request_id,
        processing_data=processing_data.model_dump(),
        current_user=current_user,
    )


# ============================================================
# 6. GET DOCUMENT REQUEST HISTORY
# ============================================================

@router.get(
    "/requests/{document_request_id}/history",
    response_model=list[DocumentRequestHistoryResponse],
)
def get_document_request_history_endpoint(
    document_request_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "document.read_self",
                "document.process",
            )
        ),
    ],
):
    """
    Retrieve document request history.

    Employee:
        Can retrieve history for own requests.

    HR/Admin:
        Can retrieve history for all document requests.

    Requires:
        document.read_self OR document.process
    """

    # HR and Admin may retrieve organization-wide history.

    if user_has_permission(
        db=db,
        user_id=current_user.user_id,
        permission_code="document.process",
    ):

        document_request = get_document_request_by_id(
            db=db,
            document_request_id=document_request_id,
        )

        if document_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document request not found",
            )

        return get_document_request_history(
            db=db,
            document_request_id=document_request_id,
        )

    # Employees can retrieve only their own history.

    return get_my_document_request_history(
        db=db,
        current_user=current_user,
        document_request_id=document_request_id,
    )
