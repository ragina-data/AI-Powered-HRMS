
"""
Leave Repository
================

Purpose:
    Centralize database queries for Leave Management.

Responsibilities:
    1. Retrieve employees and leave types.
    2. Retrieve leave entitlement rules.
    3. Retrieve employee leave balances.
    4. Retrieve and create leave requests.
    5. Detect overlapping leave applications.
    6. Retrieve and create leave approvals.
    7. Create leave transactions.
    8. Retrieve public holidays.

Transaction management:
    Database commits are handled exclusively by the service layer.

Concurrency:
    Supports PostgreSQL row-level locking when processing
    leave balances and approval decisions.
"""

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.repositories.employee_repository import (
    get_employee_by_id,
)

from app.models.leave_type import LeaveType
from app.models.leave_request import LeaveRequest
from app.models.leave_balance import LeaveBalance
from app.models.leave_entitlement_rule import LeaveEntitlementRule
from app.models.leave_approval import LeaveApproval
from app.models.leave_transaction import LeaveTransaction
from app.models.public_holiday import PublicHoliday
from sqlalchemy.dialects.postgresql import insert as pg_insert

# ============================================================
# 1. EMPLOYEE
# ============================================================

# Reuse get_employee_by_id from the existing Employee Repository.


# ============================================================
# 2. LEAVE TYPES
# ============================================================

def get_leave_type_by_code(
    db: Session,
    leave_type_code: str,
) -> LeaveType | None:
    """Retrieve a leave type using its unique code."""

    return (
        db.query(LeaveType)
        .filter(
            LeaveType.leave_type_code == leave_type_code
        )
        .first()
    )


def get_active_leave_types(
    db: Session,
) -> list[LeaveType]:
    """Retrieve all active leave types."""

    return (
        db.query(LeaveType)
        .filter(LeaveType.is_active.is_(True))
        .order_by(LeaveType.leave_type_name.asc())
        .all()
    )


# ============================================================
# 3. LEAVE ENTITLEMENT RULES
# ============================================================

def get_leave_entitlement_rule(
    db: Session,
    leave_type_id: int,
    employment_category: str,
    effective_on,
) -> LeaveEntitlementRule | None:
    """
    Retrieve the applicable active entitlement rule.

    An exact employment category takes priority over
    the general 'all' category.
    """

    return (
        db.query(LeaveEntitlementRule)
        .filter(
            LeaveEntitlementRule.leave_type_id == leave_type_id,
            LeaveEntitlementRule.is_active.is_(True),
            LeaveEntitlementRule.employment_category.in_(
                [employment_category, "all"]
            ),
            LeaveEntitlementRule.effective_from <= effective_on,
            or_(
                LeaveEntitlementRule.effective_to.is_(None),
                LeaveEntitlementRule.effective_to >= effective_on,
            ),
        )
        .order_by(
            case(
                (
                    LeaveEntitlementRule.employment_category
                    == employment_category,
                    0,
                ),
                else_=1,
            ),
            LeaveEntitlementRule.effective_from.desc(),
            LeaveEntitlementRule.entitlement_rule_id.desc(),
        )
        .first()
    )


# ============================================================
# 4. LEAVE BALANCES
# ============================================================

def get_employee_leave_balance(
    db: Session,
    employee_id: int,
    leave_type: str,
    balance_year: int,
) -> LeaveBalance | None:
    """Retrieve an employee's balance for a specific leave type and year."""

    return (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.balance_year == balance_year,
        )
        .first()
    )


def get_employee_leave_balance_for_update(
    db: Session,
    employee_id: int,
    leave_type: str,
    balance_year: int,
) -> LeaveBalance | None:
    """
    Retrieve and lock a leave balance row.

    Used during approval to prevent concurrent
    transactions from overspending the same balance.
    """

    return (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.balance_year == balance_year,
        )
        .with_for_update()
        .first()
    )


def get_employee_leave_balances(
    db: Session,
    employee_id: int,
    balance_year: int | None = None,
) -> list[LeaveBalance]:
    """Retrieve all leave balances for an employee."""

    query = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id
    )

    if balance_year is not None:
        query = query.filter(
            LeaveBalance.balance_year == balance_year
        )

    return (
        query
        .order_by(
            LeaveBalance.balance_year.desc(),
            LeaveBalance.leave_type.asc(),
        )
        .all()
    )


# ============================================================
# GET LEAVE BALANCES FOR AUTHORIZED EMPLOYEES
# ============================================================

def get_leave_balances_for_employees(
    db: Session,
    employee_ids: list[int],
    balance_year: int | None = None,
) -> list[LeaveBalance]:
    """
    Retrieve leave balances for a list of authorized employees.

    Employee visibility authorization must be performed
    in the service layer before calling this function.

    Supports optional service-year filtering.
    """

    if not employee_ids:
        return []

    query = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id.in_(employee_ids)
    )

    if balance_year is not None:
        query = query.filter(
            LeaveBalance.balance_year == balance_year
        )

    return (
        query
        .order_by(
            LeaveBalance.employee_id.asc(),
            LeaveBalance.balance_year.desc(),
            LeaveBalance.leave_type.asc(),
        )
        .all()
    )



# ============================================================
# CREATE OR RETRIEVE LEAVE BALANCE WITH ROW LOCK
# ============================================================

def get_or_create_employee_leave_balance_for_update(
    db: Session,
    employee_id: int,
    leave_type: str,
    balance_year: int,
) -> LeaveBalance:
    """
    Retrieve an employee leave balance with a row lock.

    If the balance does not exist, create it.

    PostgreSQL ON CONFLICT protects against duplicate
    balance creation during concurrent requests.

    The unique constraint used is:
        uq_employee_leave_year

    Commit is handled by the service layer.
    """

    statement = (
        pg_insert(LeaveBalance)
        .values(
            employee_id=employee_id,
            leave_type=leave_type,
            entitlement_days=0,
            used_days=0,
            balance_year=balance_year,
        )
        .on_conflict_do_nothing(
            constraint="uq_employee_leave_year"
        )
    )

    db.execute(statement)
    db.flush()

    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.balance_year == balance_year,
        )
        .with_for_update()
        .one_or_none()
    )

    if balance is None:
        raise RuntimeError(
            "Unable to retrieve or initialize employee leave balance"
        )

    return balance

# ============================================================
# 5. LEAVE REQUESTS
# ============================================================

def get_leave_request_by_id(
    db: Session,
    leave_request_id: int,
) -> LeaveRequest | None:
    """Retrieve a leave request by its primary key."""

    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.leave_request_id == leave_request_id
        )
        .first()
    )


def get_leave_request_for_update(
    db: Session,
    leave_request_id: int,
) -> LeaveRequest | None:
    """Retrieve and lock a leave request during approval processing."""

    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.leave_request_id == leave_request_id
        )
        .with_for_update()
        .first()
    )


def get_employee_leave_requests(
    db: Session,
    employee_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[LeaveRequest]:
    """Retrieve an employee's leave application history."""

    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_overlapping_leave_requests(
    db: Session,
    employee_id: int,
    start_date,
    end_date,
    exclude_request_id: int | None = None,
) -> list[LeaveRequest]:
    """
    Find pending or approved leave requests overlapping
    with the requested date range.

    Rejected and cancelled requests are excluded.
    """

    query = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(["pending", "approved"]),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date,
    )

    if exclude_request_id is not None:
        query = query.filter(
            LeaveRequest.leave_request_id != exclude_request_id
        )

    return query.all()


def create_leave_request(
    db: Session,
    request_data: dict,
) -> LeaveRequest:
    """
    Create and flush a leave application.

    Commit is handled by the service layer.
    """

    leave_request = LeaveRequest(**request_data)

    db.add(leave_request)
    db.flush()
    db.refresh(leave_request)

    return leave_request


# ============================================================
# 6. LEAVE APPROVALS
# ============================================================

def get_leave_approvals(
    db: Session,
    leave_request_id: int,
) -> list[LeaveApproval]:
    """Retrieve approval history for a leave request."""

    return (
        db.query(LeaveApproval)
        .filter(
            LeaveApproval.leave_request_id == leave_request_id
        )
        .order_by(
            LeaveApproval.decided_at.desc(),
            LeaveApproval.leave_approval_id.desc(),
        )
        .all()
    )


def create_leave_approval(
    db: Session,
    approval_data: dict,
) -> LeaveApproval:
    """Create a leave approval or rejection record."""

    approval = LeaveApproval(**approval_data)

    db.add(approval)
    db.flush()
    db.refresh(approval)

    return approval


# ============================================================
# 7. LEAVE TRANSACTIONS
# ============================================================

def create_leave_transaction(
    db: Session,
    transaction_data: dict,
) -> LeaveTransaction:
    """
    Create a leave balance ledger transaction.

    Transactions are retained as historical records.
    Commit is handled by the service layer.
    """

    transaction = LeaveTransaction(**transaction_data)

    db.add(transaction)
    db.flush()
    db.refresh(transaction)

    return transaction


# ============================================================
# GET LEAVE TRANSACTION HISTORY
# ============================================================

def get_leave_transactions_for_employees(
    db: Session,
    employee_ids: list[int],
    skip: int = 0,
    limit: int = 100,
    transaction_type: str | None = None,
    leave_type: str | None = None,
    balance_year: int | None = None,
) -> list[LeaveTransaction]:
    """
    Retrieve leave transaction history for authorized employees.

    Supports:
        1. Employee ID filtering through employee_ids.
        2. Transaction type filtering.
        3. Leave type filtering.
        4. Service-year filtering.
        5. Pagination.

    Security:
        The service layer must validate employee visibility
        before passing employee_ids to this repository.

    Transaction management:
        This function performs read-only queries.
    """

    if not employee_ids:
        return []

    query = db.query(LeaveTransaction).filter(
        LeaveTransaction.employee_id.in_(employee_ids)
    )

    if transaction_type is not None:
        query = query.filter(
            LeaveTransaction.transaction_type == transaction_type
        )

    if leave_type is not None:
        query = query.join(
            LeaveBalance,
            LeaveTransaction.leave_balance_id
            == LeaveBalance.leave_balance_id,
        ).filter(
            LeaveBalance.leave_type == leave_type
        )

    if balance_year is not None:
        if leave_type is None:
            query = query.join(
                LeaveBalance,
                LeaveTransaction.leave_balance_id
                == LeaveBalance.leave_balance_id,
            )

        query = query.filter(
            LeaveBalance.balance_year == balance_year
        )

    return (
        query
        .order_by(
            LeaveTransaction.created_at.desc(),
            LeaveTransaction.leave_transaction_id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================================================
# 8. PUBLIC HOLIDAYS
# ============================================================

def get_public_holidays(
    db: Session,
    start_date,
    end_date,
    country_code: str = "AE",
    region: str | None = None,
) -> list[PublicHoliday]:
    """
    Retrieve active public holidays within a date range.

    When a region is supplied, both country-wide and
    region-specific holidays are included.
    """

    query = db.query(PublicHoliday).filter(
        PublicHoliday.country_code == country_code,
        PublicHoliday.is_active.is_(True),
        PublicHoliday.holiday_date >= start_date,
        PublicHoliday.holiday_date <= end_date,
    )

    if region is not None:
        query = query.filter(
            PublicHoliday.region.in_(["all", region])
        )
    else:
        query = query.filter(
            PublicHoliday.region == "all"
        )

    return (
        query
        .order_by(PublicHoliday.holiday_date.asc())
        .all()
    )
