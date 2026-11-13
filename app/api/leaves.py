
"""
Leave Management API
====================

Purpose:
    Expose REST API endpoints for Leave Management.

Responsibilities:
    1. Submit leave applications.
    2. Retrieve personal leave history.
    3. Retrieve personal leave balances.
    4. Approve or reject authorized leave requests.

Security:
    All endpoints require authentication.
    Permissions are enforced through existing RBAC.
    Employees can access only their own leave information.
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

from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveApprovalCreate,
    LeaveBalanceResponse,
    LeaveTransactionResponse,
    LeaveDecisionResponse,
)

from app.repositories.leave_repository import (
    get_employee_leave_requests,
    get_employee_leave_balances,
)

from app.services.leave_service import (
    submit_leave_request,
    decide_leave_request,
    get_leave_balances_for_user,
    get_leave_transactions_for_user,
)


router = APIRouter(
    prefix="/leaves",
    tags=["Leave Management"],
)


# ============================================================
# 1. SUBMIT LEAVE REQUEST
# ============================================================

@router.post(
    "/requests",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_leave_application(
    request_data: LeaveRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("leave.request")),
    ],
):
    """
    Submit a leave application for the authenticated employee.

    Requires:
        leave.request

    New applications are created with pending status.
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to an employee profile",
        )

    return submit_leave_request(
        db=db,
        employee_id=current_user.employee_id,
        leave_type_code=request_data.leave_type,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        reason=request_data.reason,
        actor_user_id=current_user.user_id,
        medical_certificate_submitted=(
            request_data.medical_certificate_submitted
        ),
    )


# ============================================================
# 2. GET OWN LEAVE REQUESTS
# ============================================================

@router.get(
    "/requests/me",
    response_model=list[LeaveRequestResponse],
)
def get_my_leave_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("leave.read_self")),
    ],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Retrieve leave application history for the authenticated employee.

    Requires:
        leave.read_self
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to an employee profile",
        )

    return get_employee_leave_requests(
        db=db,
        employee_id=current_user.employee_id,
        skip=skip,
        limit=limit,
    )


# ============================================================
# 3. GET OWN LEAVE BALANCES
# ============================================================

@router.get(
    "/balances/me",
    response_model=list[LeaveBalanceResponse],
)
def get_my_leave_balances(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("leave.read_self")),
    ],
    balance_year: Annotated[int | None, Query()] = None,
):
    """
    Retrieve leave balances belonging to the authenticated employee.

    Requires:
        leave.read_self
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not linked to an employee profile",
        )

    return get_employee_leave_balances(
        db=db,
        employee_id=current_user.employee_id,
        balance_year=balance_year,
    )


# ============================================================
# GET AUTHORIZED LEAVE TRANSACTION HISTORY
# ============================================================

@router.get(
    "/transactions",
    response_model=list[LeaveTransactionResponse],
)
def get_leave_transaction_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "leave.read_self",
                "employee.read_team",
                "leave.manage_all",
            )
        ),
    ],
    employee_id: Annotated[int | None, Query(gt=0)] = None,
    transaction_type: Annotated[
        str | None,
        Query(max_length=20),
    ] = None,
    leave_type: Annotated[
        str | None,
        Query(max_length=30),
    ] = None,
    balance_year: Annotated[int | None, Query(gt=0)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    """
    Retrieve leave transaction history according to
    the authenticated user's employee visibility scope.

    Access:
        Employee:
            Own transactions.

        Manager:
            Own transactions and direct reports.

        HR / Admin:
            Organization-wide transactions.

    Filters:
        employee_id
        transaction_type
        leave_type
        balance_year

    Requires at least one of:
        leave.read_self
        employee.read_team
        leave.manage_all
    """

    return get_leave_transactions_for_user(
        db=db,
        current_user=current_user,
        employee_id=employee_id,
        transaction_type=transaction_type,
        leave_type=leave_type,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )

# ============================================================
# 4. GET AUTHORIZED EMPLOYEE LEAVE BALANCES
# ============================================================

@router.get(
    "/balances",
    response_model=list[LeaveBalanceResponse],
)
def get_authorized_leave_balances(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "employee.read_team",
                "leave.manage_all",
            )
        ),
    ],
    employee_id: Annotated[int | None, Query(gt=0)] = None,
    balance_year: Annotated[int | None, Query(gt=0)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    """
    Retrieve employee leave balances according to
    the authenticated user's authorization scope.

    Access:
        Manager:
            Own balances and direct reports.

        HR:
            Organization-wide balances.

        Admin:
            Organization-wide balances.

    Optional filters:
        employee_id
        balance_year
        skip
        limit

    Requires:
        employee.read_team OR leave.manage_all
    """

    return get_leave_balances_for_user(
        db=db,
        current_user=current_user,
        employee_id=employee_id,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )

# ============================================================
# 4. APPROVE / REJECT LEAVE REQUEST
# ============================================================

@router.patch(
    "/requests/{leave_request_id}/decision",
    response_model=LeaveDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def process_leave_decision(
    leave_request_id: Annotated[int, Path(gt=0)],
    decision_data: LeaveApprovalCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(
            require_permission(
                "leave.approve_team",
                "leave.manage_all",
            )
        ),
    ],
):
    """
    Approve or reject a leave application.

    Authorization:
        Manager:
            Can process leave requests for direct reports.

        HR/Admin:
            Can process leave requests across the organization
            when granted leave.manage_all.

    Requires at least one:
        leave.approve_team
        leave.manage_all
    """

    if current_user.employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver is not linked to an employee profile",
        )

    # Determine whether the authenticated user has
    # organization-wide leave administration permission.

    can_manage_all = user_has_permission(
        db=db,
        user_id=current_user.user_id,
        permission_code="leave.manage_all",
    )

    return decide_leave_request(
        db=db,
        leave_request_id=leave_request_id,
        decision=decision_data.decision,
        comments=decision_data.comments,
        approver_employee_id=current_user.employee_id,
        actor_user_id=current_user.user_id,
        can_manage_all=can_manage_all,
    )
