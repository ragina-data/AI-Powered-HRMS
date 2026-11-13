
from datetime import date
from sqlalchemy.orm import Session
from app.api.permissions import user_has_permission

from app.models.user import User
from app.services.leave_service import (
    submit_leave_request,
    decide_leave_request,
    get_leave_balances_for_user,
    get_leave_transactions_for_user,
)
from app.repositories.leave_repository import (
    get_employee_leave_requests,
)


def serialize_leave_request(leave_request) -> dict:
    """Convert a LeaveRequest ORM object to JSON-compatible data."""

    return {
        "leave_request_id": leave_request.leave_request_id,
        "employee_id": leave_request.employee_id,
        "leave_type": leave_request.leave_type,
        "start_date": (
            leave_request.start_date.isoformat()
            if leave_request.start_date else None
        ),
        "end_date": (
            leave_request.end_date.isoformat()
            if leave_request.end_date else None
        ),
        "days_requested": str(leave_request.days_requested),
        "reason": leave_request.reason,
        "status": leave_request.status,
        "submitted_at": (
            leave_request.submitted_at.isoformat()
            if leave_request.submitted_at else None
        ),
        "updated_at": (
            leave_request.updated_at.isoformat()
            if leave_request.updated_at else None
        ),
    }


def serialize_leave_balance(balance) -> dict:
    return {
        "leave_balance_id": balance.leave_balance_id,
        "employee_id": balance.employee_id,
        "leave_type": balance.leave_type,
        "entitlement_days": str(balance.entitlement_days),
        "used_days": str(balance.used_days),
        "available_days": str(balance.available_days),
        "balance_year": balance.balance_year,
        "created_at": (
            balance.created_at.isoformat()
            if balance.created_at else None
        ),
        "updated_at": (
            balance.updated_at.isoformat()
            if balance.updated_at else None
        ),
    }

def serialize_leave_transaction(transaction) -> dict:
    return {
        "leave_transaction_id": transaction.leave_transaction_id,
        "employee_id": transaction.employee_id,
        "leave_balance_id": transaction.leave_balance_id,
        "leave_request_id": transaction.leave_request_id,
        "transaction_type": transaction.transaction_type,
        "days_delta": str(transaction.days_delta),
        "notes": transaction.notes,
        "actor_user_id": transaction.actor_user_id,
        "created_at": (
            transaction.created_at.isoformat()
            if transaction.created_at else None
        ),
    }

# ============================================================
# 1. GET MY LEAVE REQUESTS
# ============================================================

def get_my_leave_requests(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> dict:

    if current_user.employee_id is None:
        raise ValueError("Account is not linked to an employee profile.")

    requests = get_employee_leave_requests(
        db=db,
        employee_id=current_user.employee_id,
        skip=skip,
        limit=limit,
    )

    return {
        "total_returned": len(requests),
        "skip": skip,
        "limit": limit,
        "leave_requests": [
            serialize_leave_request(item)
            for item in requests
        ],
    }


# ============================================================
# 2. GET MY LEAVE BALANCE
# ============================================================

def get_my_leave_balance(
    db: Session,
    current_user: User,
    balance_year: int | None = None,
) -> list[dict]:

    balances = get_leave_balances_for_user(
        db=db,
        current_user=current_user,
        employee_id=current_user.employee_id,
        balance_year=balance_year,
    )

    return [
        serialize_leave_balance(balance)
        for balance in balances
    ]


# ============================================================
# 3. GET AUTHORIZED LEAVE BALANCES
# ============================================================

def get_authorized_leave_balances(
    db: Session,
    current_user: User,
    employee_id: int | None = None,
    balance_year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:

    balances = get_leave_balances_for_user(
        db=db,
        current_user=current_user,
        employee_id=employee_id,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_leave_balance(balance)
        for balance in balances
    ]


# ============================================================
# 4. GET MY LEAVE TRANSACTIONS
# ============================================================

def get_my_leave_transactions(
    db: Session,
    current_user: User,
    transaction_type: str | None = None,
    leave_type: str | None = None,
    balance_year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:

    transactions = get_leave_transactions_for_user(
        db=db,
        current_user=current_user,
        employee_id=current_user.employee_id,
        transaction_type=transaction_type,
        leave_type=leave_type,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_leave_transaction(item)
        for item in transactions
    ]


# ============================================================
# 5. GET AUTHORIZED LEAVE TRANSACTIONS
# ============================================================

def get_authorized_leave_transactions(
    db: Session,
    current_user: User,
    employee_id: int | None = None,
    transaction_type: str | None = None,
    leave_type: str | None = None,
    balance_year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:

    transactions = get_leave_transactions_for_user(
        db=db,
        current_user=current_user,
        employee_id=employee_id,
        transaction_type=transaction_type,
        leave_type=leave_type,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )

    return [
        serialize_leave_transaction(item)
        for item in transactions
    ]


# ============================================================
# 6. SUBMIT LEAVE REQUEST
# ============================================================

def submit_leave_request_handler(
    db: Session,
    current_user: User,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: str | None = None,
    medical_certificate_submitted: bool = False,
) -> dict:

    if current_user.employee_id is None:
        raise ValueError("Account is not linked to an employee profile.")

    return submit_leave_request(
        db=db,
        employee_id=current_user.employee_id,
        leave_type_code=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        actor_user_id=current_user.user_id,
        medical_certificate_submitted=medical_certificate_submitted,
    )


# ============================================================
# 7. APPROVE / REJECT LEAVE REQUEST
# ============================================================

def decide_leave_request_handler(
    db: Session,
    current_user: User,
    leave_request_id: int,
    decision: str,
    comments: str | None = None,
) -> dict:
    """
    Process a leave decision using the existing
    leave service and permission system.
    """

    if current_user.employee_id is None:
        raise ValueError(
            "Approver must have a linked employee profile."
        )

    can_manage_all = user_has_permission(
        db=db,
        user_id=current_user.user_id,
        permission_code="leave.manage_all",
    )

    return decide_leave_request(
        db=db,
        leave_request_id=leave_request_id,
        decision=decision,
        comments=comments,
        approver_employee_id=current_user.employee_id,
        actor_user_id=current_user.user_id,
        can_manage_all=can_manage_all,
    )