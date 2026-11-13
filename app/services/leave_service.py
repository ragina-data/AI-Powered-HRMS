
"""
Leave Service
=============

Purpose:
    Implement business logic for Leave Management.

Responsibilities:
    1. Validate employee eligibility.
    2. Validate leave types.
    3. Enforce leave notice requirements.
    4. Validate maximum consecutive leave days.
    5. Prevent overlapping leave requests.
    6. Record leave audit events.

Transaction management:
    Database commits are handled by service operations.
"""
from datetime import date, datetime,timedelta, timezone

from decimal import Decimal
from zoneinfo import ZoneInfo
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import leave_type
from app.models.audit_log import AuditLog
from calendar import monthrange
from app.models.leave_transaction import LeaveTransaction

from app.models.leave_balance import LeaveBalance
from app.repositories.employee_repository import (
    get_employee_by_id,
    get_employees,
)

from app.repositories.leave_repository import (
    get_leave_type_by_code,
    get_overlapping_leave_requests,
    create_leave_request,
    get_leave_request_for_update,
    get_employee_leave_balance_for_update,
    create_leave_approval,
    create_leave_transaction,
    get_or_create_employee_leave_balance_for_update,
    get_employee_leave_balance,
    get_leave_balances_for_employees,
    get_leave_transactions_for_employees,
)
from app.services.employee_service import (
    get_employee_visibility_scope,
)
# ============================================================
# LEAVE POLICY CONFIGURATION
# ============================================================

PROBATION_PERIOD_MONTHS = 6

# ============================================================
# MEDICAL / SICK LEAVE POLICY
# ============================================================

SICK_LEAVE_FULL_PAY_DAYS = Decimal("15")
SICK_LEAVE_HALF_PAY_DAYS = Decimal("30")
SICK_LEAVE_UNPAID_DAYS = Decimal("45")

SICK_LEAVE_MAX_DAYS = Decimal("90")
# ============================================================
# 1. LEAVE AUDIT LOGGING
# ============================================================

def record_leave_audit(
    db: Session,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None,
    details: dict | None = None,
) -> AuditLog:
    """
    Add a Leave Management audit record.

    The calling service function is responsible
    for committing or rolling back the transaction.
    """

    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=(
            str(entity_id)
            if entity_id is not None
            else None
        ),
        details=details or {},
    )

    db.add(audit_log)

    return audit_log


# ============================================================
# 2. VALIDATE LEAVE APPLICATION
# ============================================================

def validate_leave_application(
    db: Session,
    employee_id: int,
    leave_type_code: str,
    start_date: date,
    end_date: date,
    exclude_request_id: int | None = None,
    today: date | None = None,
) -> dict:
    """
    Validate an employee's leave application.

    Validations:
        1. Employee exists.
        2. Employee is active.
        3. Leave type exists and is active.
        4. Start date does not exceed the notice restriction.
        5. Maximum consecutive days are respected.
        6. Existing pending/approved leave does not overlap.

    Returns:
        Validated employee, leave type and requested days.

    Date calculation:
        Inclusive calendar days.
    """

    # --------------------------------------------------------
    # STEP 1: Validate date range.
    # --------------------------------------------------------

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave end date cannot be before start date",
        )

    # --------------------------------------------------------
    # STEP 2: Retrieve employee.
    # --------------------------------------------------------

    employee = get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # --------------------------------------------------------
    # STEP 3: Validate employee status.
    # --------------------------------------------------------

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive employees cannot submit leave requests",
        )

    # --------------------------------------------------------
    # STEP 4: Retrieve leave type.
    # --------------------------------------------------------

    normalized_leave_type = leave_type_code.strip().lower()

    leave_type = get_leave_type_by_code(
        db,
        normalized_leave_type,
    )

    if leave_type is None or not leave_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive leave type",
        )

    # --------------------------------------------------------
    # STEP 5: Validate minimum notice period.
    # --------------------------------------------------------

    if today is None:
        today = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    notice_days = (
        start_date - today
    ).days

    minimum_notice_days = (
        leave_type.min_notice_calendar_days
    )

    if notice_days < minimum_notice_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{leave_type.leave_type_name} requires "
                f"at least {minimum_notice_days} calendar "
                f"days of advance notice"
            ),
        )

    # --------------------------------------------------------
    # STEP 6: Calculate requested calendar days.
    # --------------------------------------------------------

    days_requested = Decimal(
        (end_date - start_date).days + 1
    )

    # --------------------------------------------------------
    # STEP 7: Validate maximum consecutive leave days.
    # --------------------------------------------------------

    maximum_days = leave_type.max_consecutive_days

    if (
        maximum_days is not None
        and days_requested > Decimal(maximum_days)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maximum consecutive leave duration "
                f"for {leave_type.leave_type_name} "
                f"is {maximum_days} days"
            ),
        )

    # --------------------------------------------------------
    # STEP 8: Check overlapping applications.
    # --------------------------------------------------------

    overlapping_requests = get_overlapping_leave_requests(
        db=db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        exclude_request_id=exclude_request_id,
    )

    if overlapping_requests:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Leave application overlaps with an "
                "existing pending or approved leave request"
            ),
        )

    # --------------------------------------------------------
    # STEP 9: Return validated information.
    # --------------------------------------------------------

    return {
        "employee": employee,
        "leave_type": leave_type,
        "days_requested": days_requested,
    }


# ============================================================
# 3. SUBMIT LEAVE REQUEST
# ============================================================

def submit_leave_request(
    db: Session,
    employee_id: int,
    leave_type_code: str,
    start_date: date,
    end_date: date,
    reason: str | None,
    actor_user_id: int,
    medical_certificate_submitted: bool = False,
) -> dict:
    """
    Submit a new employee leave application.

    Workflow:
        1. Validate employee and leave eligibility.
        2. Validate leave application details.
        3. Calculate requested days.
        4. Create leave request with pending status.
        5. Record audit history.
        6. Commit the transaction.

    Important:
        Leave balances are NOT deducted during submission.
        Balance deduction happens only after approval.
    """

    # STEP 1: Validate the application.

    validation = validate_leave_application(
        db=db,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        start_date=start_date,
        end_date=end_date,
    )
    if (
        medical_certificate_submitted
        and leave_type.leave_type_code != "sick"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical certificate submission applies only to sick leave",
    )

    employee = validation["employee"]
    leave_type = validation["leave_type"]
    days_requested = validation["days_requested"]

    try:

        # STEP 2: Create the leave request.

        leave_request = create_leave_request(
            db,
            {
                "employee_id": employee.employee_id,
                "leave_type": leave_type.leave_type_code,
                "start_date": start_date,
                "end_date": end_date,
                "days_requested": days_requested,
                "reason": reason,
                "medical_certificate_submitted": medical_certificate_submitted,
                "status": "pending",
            },
        )

        # STEP 3: Record audit history.

        record_leave_audit(
            db=db,
            actor_user_id=actor_user_id,
            action="LEAVE_REQUEST_CREATED",
            entity_type="LeaveRequest",
            entity_id=leave_request.leave_request_id,
            details={
                "employee_id": employee.employee_id,
                "employee_code": employee.employee_code,
                "leave_type": leave_type.leave_type_code,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_requested": str(days_requested),
                "status": "pending",
                "medical_certificate_submitted": medical_certificate_submitted,
            },
        )

        # STEP 4: Commit request and audit record together.

        db.commit()
        db.refresh(leave_request)

        return {
            "leave_request_id": leave_request.leave_request_id,
            "employee_id": leave_request.employee_id,
            "leave_type": leave_request.leave_type,
            "start_date": leave_request.start_date,
            "end_date": leave_request.end_date,
            "days_requested": leave_request.days_requested,
            "reason": leave_request.reason,
            "medical_certificate_submitted": leave_request.medical_certificate_submitted,
            "status": leave_request.status,
            "submitted_at": leave_request.submitted_at,
            "updated_at": leave_request.updated_at,
        }

    except Exception:
        db.rollback()
        raise

# ============================================================
# 4. APPROVE / REJECT LEAVE REQUEST
# ============================================================

def decide_leave_request(
    db: Session,
    leave_request_id: int,
    decision: str,
    comments: str | None,
    approver_employee_id: int,
    actor_user_id: int,
    can_manage_all: bool = False,
) -> dict:
    """
    Approve or reject a pending employee leave request.

    Authorization:
        - Managers can decide for direct reports.
        - HR/Admin with leave.manage_all can decide
          across the organization.
        - Employees cannot approve their own requests.

    Approval:
        - Paid leave requires an existing sufficient balance.
        - Balance deductions and ledger transactions are atomic.

    Rejection:
        - No leave balance is deducted.

    Unpaid leave:
        - Does not deduct paid leave balances.
    """

    try:

        # ----------------------------------------------------
        # STEP 1: Validate decision.
        # ----------------------------------------------------

        if decision not in ("approved", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid leave decision",
            )

        # ----------------------------------------------------
        # STEP 2: Retrieve and lock the leave request.
        # ----------------------------------------------------

        leave_request = get_leave_request_for_update(
            db,
            leave_request_id,
        )

        if leave_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found",
            )

        if leave_request.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending leave requests can be processed",
            )

        # ----------------------------------------------------
        # STEP 3: Validate the approver.
        # ----------------------------------------------------

        if approver_employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Approver must have a linked employee profile",
            )

        approver = get_employee_by_id(
            db,
            approver_employee_id,
        )

        if approver is None or not approver.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Approver employee profile is unavailable",
            )

        # ----------------------------------------------------
        # STEP 4: Prevent self-approval.
        # ----------------------------------------------------

        if leave_request.employee_id == approver_employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees cannot approve their own leave requests",
            )

        # ----------------------------------------------------
        # STEP 5: Validate manager reporting relationship.
        # ----------------------------------------------------

        requesting_employee = get_employee_by_id(
            db,
            leave_request.employee_id,
        )

        if requesting_employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requesting employee not found",
            )

        if not can_manage_all:

            if (
                requesting_employee.manager_employee_id
                != approver_employee_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Managers can only approve leave requests "
                        "from their direct reports"
                    ),
                )

        # ----------------------------------------------------
        # STEP 6: Retrieve leave type.
        # ----------------------------------------------------

        leave_type = get_leave_type_by_code(
            db,
            leave_request.leave_type,
        )

        if leave_type is None or not leave_type.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave type is unavailable",
            )

        # ----------------------------------------------------

        # ----------------------------------------------------
        # STEP 7: PROCESS LEAVE BALANCES ON APPROVAL.
        # ----------------------------------------------------

        balance_deductions = []
        sick_leave_pay_breakdown = []

        if (
            decision == "approved"
            and leave_type.leave_type_code == "sick"
        ):

            # ------------------------------------------------
            # 7A. Validate employee hire date.
            # ------------------------------------------------

            if requesting_employee.hire_date is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Employee hire date is required "
                        "for sick leave calculation"
                    ),
                )

            # ------------------------------------------------
            # 7B. Split sick leave by probation and
            #     employee service year.
            # ------------------------------------------------

            sick_segments = split_sick_leave_by_probation_and_service_year(
                hire_date=requesting_employee.hire_date,
                start_date=leave_request.start_date,
                end_date=leave_request.end_date,
            )

            # ------------------------------------------------
            # 7C. Process each service year separately.
            # ------------------------------------------------

            for balance_year, segment in sorted(
                sick_segments.items()
            ):

                probation_days = segment[
                    "probation_unpaid_days"
                ]

                post_probation_days = segment[
                    "post_probation_days"
                ]

                year_breakdown = {
                    "balance_year": balance_year,
                    "probation_unpaid_days": str(probation_days),
                    "post_probation_days": str(post_probation_days),
                    "full_pay_days": "0",
                    "half_pay_days": "0",
                    "unpaid_days": str(probation_days),
                }

                # --------------------------------------------
                # 7D. Calculate post-probation sick leave.
                # --------------------------------------------

                if post_probation_days > 0:

                    leave_balance = get_employee_leave_balance_for_update(
                        db=db,
                        employee_id=leave_request.employee_id,
                        leave_type="sick",
                        balance_year=balance_year,
                    )

                    if leave_balance is None:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"Sick leave balance is not configured "
                                f"for service year {balance_year}"
                            ),
                        )

                    entitlement = Decimal(
                        str(leave_balance.entitlement_days)
                    )

                    used_days = Decimal(
                        str(leave_balance.used_days)
                    )

                    # The sick leave statutory tracking balance
                    # must accommodate the 90-day service-year limit.

                    if entitlement < SICK_LEAVE_MAX_DAYS:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                "Sick leave entitlement must be "
                                "configured for at least 90 days "
                                f"for service year {balance_year}"
                            ),
                        )

                    # Calculate cumulative salary entitlement.

                    pay_tiers = calculate_sick_leave_pay_tiers(
                        already_used_days=used_days,
                        requested_days=post_probation_days,
                    )

                    # ----------------------------------------
                    # 7E. Update sick leave balance.
                    # ----------------------------------------

                    new_used_days = (
                        used_days + post_probation_days
                    )

                    leave_balance.used_days = new_used_days

                    leave_balance.updated_at = datetime.now(
                        timezone.utc
                    )

                    # ----------------------------------------
                    # 7F. Record sick leave usage transaction.
                    # ----------------------------------------

                    create_leave_transaction(
                        db,
                        {
                            "employee_id": leave_request.employee_id,
                            "leave_balance_id": leave_balance.leave_balance_id,
                            "leave_request_id": leave_request.leave_request_id,
                            "transaction_type": "usage",
                            "days_delta": -post_probation_days,
                            "notes": (
                                f"Approved sick leave for service year "
                                f"{balance_year}. "
                                f"Full pay: {pay_tiers['full_pay_days']}, "
                                f"Half pay: {pay_tiers['half_pay_days']}, "
                                f"Unpaid: {pay_tiers['unpaid_days']}"
                            ),
                            "actor_user_id": actor_user_id,
                        },
                    )

                    # ----------------------------------------
                    # 7G. Store salary-tier calculation.
                    # ----------------------------------------

                    year_breakdown.update({
                        "full_pay_days": str(
                            pay_tiers["full_pay_days"]
                        ),
                        "half_pay_days": str(
                            pay_tiers["half_pay_days"]
                        ),
                        "unpaid_days": str(
                            Decimal(str(pay_tiers["unpaid_days"]))
                            + probation_days
                        ),
                        "previously_used_days": str(used_days),
                        "total_used_days": str(
                            pay_tiers["total_used_days"]
                        ),
                        "remaining_sick_leave_days": str(
                            pay_tiers["remaining_sick_leave_days"]
                        ),
                    })

                    # ----------------------------------------
                    # 7H. Record balance deduction audit.
                    # ----------------------------------------

                    record_leave_audit(
                        db=db,
                        actor_user_id=actor_user_id,
                        action="LEAVE_BALANCE_DEBITED",
                        entity_type="LeaveBalance",
                        entity_id=leave_balance.leave_balance_id,
                        details={
                            "employee_id": leave_request.employee_id,
                            "leave_request_id": leave_request.leave_request_id,
                            "leave_type": "sick",
                            "balance_year": balance_year,
                            "days_deducted": str(post_probation_days),
                            "full_pay_days": str(
                                pay_tiers["full_pay_days"]
                            ),
                            "half_pay_days": str(
                                pay_tiers["half_pay_days"]
                            ),
                            "unpaid_days": str(
                                pay_tiers["unpaid_days"]
                            ),
                        },
                    )

                    balance_deductions.append({
                        "balance_year": balance_year,
                        "leave_type": "sick",
                        "days_deducted": str(post_probation_days),
                    })

                sick_leave_pay_breakdown.append(
                    year_breakdown
                )

        # ----------------------------------------------------
        # STEP 7I: PROCESS OTHER PAID LEAVE TYPES.
        # ----------------------------------------------------

        elif decision == "approved" and leave_type.is_paid:

            if requesting_employee.hire_date is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Employee hire date is required "
                        "for service-year leave accounting"
                    ),
                )

            # Split leave using employee service years.

            days_by_service_year = split_leave_days_by_service_year(
                hire_date=requesting_employee.hire_date,
                start_date=leave_request.start_date,
                end_date=leave_request.end_date,
            )

            for balance_year, requested_days in sorted(
                days_by_service_year.items()
            ):

                leave_balance = get_employee_leave_balance_for_update(
                    db=db,
                    employee_id=leave_request.employee_id,
                    leave_type=leave_request.leave_type,
                    balance_year=balance_year,
                )

                if leave_balance is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Leave balance is not configured for "
                            f"{leave_request.leave_type} in "
                            f"{balance_year}"
                        ),
                    )

                entitlement = Decimal(
                    str(leave_balance.entitlement_days)
                )

                used_days = Decimal(
                    str(leave_balance.used_days)
                )

                available_days = entitlement - used_days

                if available_days < requested_days:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Insufficient {leave_request.leave_type} "
                            f"leave balance for {balance_year}. "
                            f"Available: {available_days}, "
                            f"Requested: {requested_days}"
                        ),
                    )

                leave_balance.used_days = (
                    used_days + requested_days
                )

                leave_balance.updated_at = datetime.now(
                    timezone.utc
                )

                create_leave_transaction(
                    db,
                    {
                        "employee_id": leave_request.employee_id,
                        "leave_balance_id": leave_balance.leave_balance_id,
                        "leave_request_id": leave_request.leave_request_id,
                        "transaction_type": "usage",
                        "days_delta": -requested_days,
                        "notes": (
                            f"Approved {leave_request.leave_type} "
                            f"leave for service year {balance_year}"
                        ),
                        "actor_user_id": actor_user_id,
                    },
                )

                record_leave_audit(
                    db=db,
                    actor_user_id=actor_user_id,
                    action="LEAVE_BALANCE_DEBITED",
                    entity_type="LeaveBalance",
                    entity_id=leave_balance.leave_balance_id,
                    details={
                        "employee_id": leave_request.employee_id,
                        "leave_request_id": leave_request.leave_request_id,
                        "leave_type": leave_request.leave_type,
                        "balance_year": balance_year,
                        "days_deducted": str(requested_days),
                    },
                )

                balance_deductions.append({
                    "balance_year": balance_year,
                    "days_deducted": str(requested_days),
                })

        # ----------------------------------------------------
        # STEP 8: Record approval or rejection.
        # ----------------------------------------------------

        leave_request.status = decision
        leave_request.updated_at = datetime.now(timezone.utc)

        approval = create_leave_approval(
            db,
            {
                "leave_request_id": leave_request.leave_request_id,
                "approver_employee_id": approver_employee_id,
                "decision": decision,
                "comments": comments,
            },
        )

        # ----------------------------------------------------
        # STEP 9: Record decision audit event.
        # ----------------------------------------------------

        record_leave_audit(
            db=db,
            actor_user_id=actor_user_id,
            action=(
                "LEAVE_REQUEST_APPROVED"
                if decision == "approved"
                else "LEAVE_REQUEST_REJECTED"
            ),
            entity_type="LeaveRequest",
            entity_id=leave_request.leave_request_id,
            details={
                "employee_id": leave_request.employee_id,
                "approver_employee_id": approver_employee_id,
                "decision": decision,
                "comments": comments,
                "days_requested": str(
                    leave_request.days_requested
                ),
                "balance_deductions": balance_deductions,
                "medical_certificate_submitted": (
                    leave_request.medical_certificate_submitted
                ),
                "sick_leave_pay_breakdown": sick_leave_pay_breakdown,
            },
        )

        # ----------------------------------------------------
        # STEP 10: Commit everything atomically.
        # ----------------------------------------------------

        db.commit()
        db.refresh(leave_request)

        return {
            "leave_request_id": leave_request.leave_request_id,
            "employee_id": leave_request.employee_id,
            "leave_type": leave_request.leave_type,
            "start_date": leave_request.start_date,
            "end_date": leave_request.end_date,
            "days_requested": leave_request.days_requested,
            "reason": leave_request.reason,
            "status": leave_request.status,
            "approval_id": approval.leave_approval_id,
            "approver_employee_id": approver_employee_id,
            "balance_deductions": balance_deductions,
            "medical_certificate_submitted": (
                leave_request.medical_certificate_submitted
            ),
            "sick_leave_pay_breakdown": sick_leave_pay_breakdown,
        }

    except Exception:
        db.rollback()
        raise

# ============================================================
# 5. ANNUAL LEAVE ELIGIBILITY CALCULATION
# ============================================================

def _add_calendar_months(
    start_date: date,
    months: int,
) -> date:
    """
    Add calendar months while handling month-end dates.

    Example:
        31 January + 1 month = 28 February
    """

    month_index = start_date.month - 1 + months

    year = start_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        start_date.day,
        monthrange(year, month)[1],
    )

    return date(year, month, day)


def _calculate_completed_service_months(
    hire_date: date,
    as_of_date: date,
) -> int:
    """Calculate completed calendar months of service."""

    months = (
        (as_of_date.year - hire_date.year) * 12
        + as_of_date.month
        - hire_date.month
    )

    if _add_calendar_months(hire_date, months) > as_of_date:
        months -= 1

    return max(months, 0)


def calculate_annual_leave_entitlement(
    hire_date: date,
    as_of_date: date | None = None,
) -> dict:
    """
    Determine statutory annual leave eligibility
    for a full-time employee covered by UAE private-sector law.

    Rules:
        Less than 6 months:
            No statutory annual leave entitlement yet.

        6 months to less than 1 year:
            2 calendar days per month of service.

        1 year or more:
            At least 30 calendar days per service year.

    Important:
        This calculates the entitlement category and rate.
        It does not calculate available balance or account
        for previously consumed or carried-forward leave.
    """

    # STEP 1: Validate hire date.

    if hire_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee hire date is required for annual leave calculation",
        )

    # STEP 2: Determine calculation date.

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    if hire_date > as_of_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee hire date cannot be in the future",
        )

    # STEP 3: Calculate completed service months.

    service_months = _calculate_completed_service_months(
        hire_date,
        as_of_date,
    )

    # STEP 4: Employees with less than six months.

    six_month_anniversary = _add_calendar_months(
        hire_date,
        6,
    )

    if as_of_date < six_month_anniversary:
            return {
            "eligible": False,
            "eligibility_status": "not_yet_eligible",
            "hire_date": hire_date,
            "as_of_date": as_of_date,
            "completed_service_months": service_months,
            "completed_service_years": 0,
            "entitlement_days": Decimal("0"),
            "entitlement_basis": "No statutory annual leave entitlement before six months of service",
        }

    # STEP 5: Employees between six months and one year.

    if service_months < 12:

        entitlement_days = Decimal(
            service_months * 2
        )

        return {
            "eligible": True,
            "eligibility_status": "monthly_entitlement",
            "hire_date": hire_date,
            "as_of_date": as_of_date,
            "completed_service_months": service_months,
            "completed_service_years": 0,
            "entitlement_days": entitlement_days,
            "entitlement_basis": "2 calendar days per month of service",
        }

    # STEP 6: Employees who completed at least one year.

    completed_years = service_months // 12

    return {
        "eligible": True,
        "eligibility_status": "annual_entitlement",
        "hire_date": hire_date,
        "as_of_date": as_of_date,
        "completed_service_months": service_months,
        "completed_service_years": completed_years,
        "entitlement_days": Decimal("30"),
        "entitlement_basis": "At least 30 calendar days per year of service",
    }


# ============================================================
# 6. EMPLOYEE SERVICE YEAR PERIOD
# ============================================================

def get_employee_service_year_period(
    hire_date: date,
    reference_date: date,
) -> dict:
    """
    Calculate the employee's service-year period.

    Example:
        Hire date: 15 March 2026

        Service year 1:
            15 March 2026 - 14 March 2027

        Service year 2:
            15 March 2027 - 14 March 2028

    balance_year identifies the year in which
    the service period begins.
    """

    if hire_date is None:
        raise ValueError("Employee hire date is required")

    if reference_date < hire_date:
        raise ValueError(
            "Reference date cannot be before employee hire date"
        )

    completed_months = _calculate_completed_service_months(
        hire_date,
        reference_date,
    )

    completed_years = completed_months // 12

    period_start = _add_calendar_months(
        hire_date,
        completed_years * 12,
    )

    next_period_start = _add_calendar_months(
        hire_date,
        (completed_years + 1) * 12,
    )

    period_end = next_period_start - timedelta(days=1)

    return {
        "service_year": completed_years + 1,
        "balance_year": period_start.year,
        "start_date": period_start,
        "end_date": period_end,
    }


# ============================================================
# 7. SPLIT LEAVE DAYS BY EMPLOYEE SERVICE YEAR
# ============================================================

def split_leave_days_by_service_year(
    hire_date: date,
    start_date: date,
    end_date: date,
) -> dict[int, Decimal]:
    """
    Split requested inclusive calendar days across
    employee service-year balance periods.

    Returns:
        Dictionary containing balance_year and
        requested days for each service year.

    Example:
        Hire date: 15 March 2026

        Leave:
            12 March 2027 - 18 March 2027

        Result:
            {
                2026: Decimal("3"),
                2027: Decimal("4")
            }
    """

    if start_date < hire_date:
        raise ValueError(
            "Leave cannot start before employee hire date"
        )

    if end_date < start_date:
        raise ValueError(
            "Leave end date cannot be before start date"
        )

    days_by_service_year: dict[int, Decimal] = {}

    current_date = start_date

    while current_date <= end_date:

        period = get_employee_service_year_period(
            hire_date=hire_date,
            reference_date=current_date,
        )

        balance_year = period["balance_year"]

        segment_end = min(
            end_date,
            period["end_date"],
        )

        segment_days = Decimal(
            (segment_end - current_date).days + 1
        )

        days_by_service_year[balance_year] = (
            days_by_service_year.get(
                balance_year,
                Decimal("0"),
            )
            + segment_days
        )

        current_date = segment_end + timedelta(days=1)

    return days_by_service_year


# ============================================================
# 8. MEDICAL / SICK LEAVE ELIGIBILITY
# ============================================================

def is_paid_sick_leave_eligible(
    hire_date: date,
    as_of_date: date | None = None,
) -> bool:
    """
    Determine whether the employee has completed
    the configured probation period.

    Uses the existing employees.hire_date field.
    No database changes are required.
    """

    if hire_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee hire date is required",
        )

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    if as_of_date < hire_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calculation date cannot precede hire date",
        )

    probation_completion_date = _add_calendar_months(
        hire_date,
        PROBATION_PERIOD_MONTHS,
    )

    return as_of_date >= probation_completion_date

# ============================================================
# 9. CALCULATE MEDICAL LEAVE PAY TIERS
# ============================================================

def calculate_sick_leave_pay_tiers(
    already_used_days: Decimal,
    requested_days: Decimal,
) -> dict:
    """
    Calculate sick leave salary entitlement.

    UAE private-sector statutory structure:

        First 15 days:
            Full pay.

        Next 30 days:
            Half pay.

        Remaining 45 days:
            Unpaid.

    The calculation uses cumulative sick leave
    already consumed in the employee's service year.

    This function calculates eligible day categories.
    Actual salary amounts are handled by payroll.

    Assumption:
        Employee has completed probation.

    Returns:
        Full-pay days.
        Half-pay days.
        Unpaid days.
        Updated cumulative usage.
    """

    # --------------------------------------------------------
    # STEP 1: Convert inputs to Decimal.
    # --------------------------------------------------------

    already_used_days = Decimal(str(already_used_days))
    requested_days = Decimal(str(requested_days))

    # --------------------------------------------------------
    # STEP 2: Validate inputs.
    # --------------------------------------------------------

    if not already_used_days.is_finite():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid previous sick leave usage",
        )

    if not requested_days.is_finite():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid requested sick leave duration",
        )

    if already_used_days < 0 or already_used_days > SICK_LEAVE_MAX_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous sick leave usage is outside the permitted range",
        )

    if requested_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested sick leave days must be greater than zero",
        )

    # --------------------------------------------------------
    # STEP 3: Validate maximum statutory sick leave.
    # --------------------------------------------------------

    total_after_request = (
        already_used_days + requested_days
    )

    if total_after_request > SICK_LEAVE_MAX_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The employee has exceeded the maximum "
                "90-day sick leave entitlement for the service year"
            ),
        )

    # --------------------------------------------------------
    # STEP 4: Calculate remaining full-pay entitlement.
    # --------------------------------------------------------

    full_pay_remaining = max(
        Decimal("0"),
        SICK_LEAVE_FULL_PAY_DAYS - already_used_days,
    )

    full_pay_days = min(
        requested_days,
        full_pay_remaining,
    )

    remaining_days = requested_days - full_pay_days

    # --------------------------------------------------------
    # STEP 5: Calculate remaining half-pay entitlement.
    # --------------------------------------------------------

    cumulative_after_full_pay = (
        already_used_days + full_pay_days
    )

    half_pay_limit = (
        SICK_LEAVE_FULL_PAY_DAYS
        + SICK_LEAVE_HALF_PAY_DAYS
    )

    half_pay_remaining = max(
        Decimal("0"),
        half_pay_limit - cumulative_after_full_pay,
    )

    half_pay_days = min(
        remaining_days,
        half_pay_remaining,
    )

    remaining_days -= half_pay_days

    # --------------------------------------------------------
    # STEP 6: Calculate unpaid entitlement.
    # --------------------------------------------------------

    unpaid_days = remaining_days

    # --------------------------------------------------------
    # STEP 7: Return calculation.
    # --------------------------------------------------------

    return {
        "previously_used_days": already_used_days,
        "requested_days": requested_days,
        "full_pay_days": full_pay_days,
        "half_pay_days": half_pay_days,
        "unpaid_days": unpaid_days,
        "total_used_days": total_after_request,
        "remaining_sick_leave_days": (
            SICK_LEAVE_MAX_DAYS - total_after_request
        ),
    }


# ============================================================
# 10. SPLIT SICK LEAVE BY PROBATION AND SERVICE YEAR
# ============================================================

def split_sick_leave_by_probation_and_service_year(
    hire_date: date,
    start_date: date,
    end_date: date,
) -> dict:
    """
    Split sick leave into probation and post-probation
    days, grouped by employee service year.

    Probation days:
        Unpaid sick leave, subject to medical evidence.

    Post-probation days:
        Subject to statutory 15/30/45 salary tiers.

    No database changes are performed.
    """

    if hire_date is None:
        raise ValueError("Employee hire date is required")

    if start_date < hire_date:
        raise ValueError("Sick leave cannot start before hire date")

    if end_date < start_date:
        raise ValueError("Invalid sick leave date range")

    probation_end_date = _add_calendar_months(
        hire_date,
        PROBATION_PERIOD_MONTHS,
    )

    result = {}
    current_date = start_date

    while current_date <= end_date:

        service_period = get_employee_service_year_period(
            hire_date=hire_date,
            reference_date=current_date,
        )

        balance_year = service_period["balance_year"]

        is_probation = current_date < probation_end_date

        if is_probation:
            segment_end = min(
                end_date,
                service_period["end_date"],
                probation_end_date - timedelta(days=1),
            )
            category = "probation_unpaid_days"

        else:
            segment_end = min(
                end_date,
                service_period["end_date"],
            )
            category = "post_probation_days"

        segment_days = Decimal(
            (segment_end - current_date).days + 1
        )

        if balance_year not in result:
            result[balance_year] = {
                "probation_unpaid_days": Decimal("0"),
                "post_probation_days": Decimal("0"),
            }

        result[balance_year][category] += segment_days

        current_date = segment_end + timedelta(days=1)

    return result

# ============================================================
# 11. CALCULATE MONTHLY ANNUAL LEAVE ACCRUAL
# ============================================================

def calculate_annual_leave_accrual_target(
    hire_date: date,
    balance_year: int,
    as_of_date: date | None = None,
) -> Decimal:
    """
    Calculate the target annual leave entitlement for
    one employee service-year balance.

    First service year:
        Before 6 months: 0 days.
        From 6 months to less than 1 year:
            2 days per completed service month.
        At completion of 1 year:
            30 days.

    Subsequent service years:
        2.5 days per completed service month.
        Maximum 30 days per service year.

    balance_year:
        Calendar year in which the employee service
        year begins.

    Returns:
        Target entitlement in days.

    This function does not modify the database.
    """

    # STEP 1: Validate hire date.

    if hire_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee hire date is required",
        )

    # STEP 2: Determine calculation date.

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    if hire_date > as_of_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hire date cannot be in the future",
        )

    # STEP 3: Identify the requested service year.

    service_year_number = (
        balance_year - hire_date.year + 1
    )

    if service_year_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid employee service year",
        )

    period_start = _add_calendar_months(
        hire_date,
        (service_year_number - 1) * 12,
    )

    if period_start.year != balance_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance year does not match employee service year",
        )

    next_period_start = _add_calendar_months(
        hire_date,
        service_year_number * 12,
    )

    # STEP 4: Do not credit future service years.

    if as_of_date < period_start:
        return Decimal("0")

    # STEP 5: Calculate completed months in this period.

    if as_of_date >= next_period_start:
        completed_months = 12
    else:
        completed_months = _calculate_completed_service_months(
            period_start,
            as_of_date,
        )

    # STEP 6: First service year.

   # STEP 6: First service year.

    if service_year_number == 1:

        six_month_anniversary = _add_calendar_months(
            hire_date,
            6,
        )

        # No statutory entitlement before completing six months.
        if as_of_date < six_month_anniversary:
            return Decimal("0")

        # At the first service anniversary,
        # the entitlement must reach 30 days.
        if as_of_date >= next_period_start:
            return Decimal("30")

        # Between six months and one year:
        # 2 days per completed service month.
        entitlement = (
            Decimal(completed_months)
            * Decimal("2")
        )

        return min(
            entitlement,
            Decimal("30"),
        )
    # STEP 7: Subsequent service years.
    # Monthly accrual = 30 / 12 = 2.5 days.

    entitlement = (
        Decimal(completed_months)
        * Decimal("2.5")
    )

    return min(
        entitlement,
        Decimal("30"),
    )


# ============================================================
# 12. ACCRUE ANNUAL LEAVE FOR ONE EMPLOYEE
# ============================================================

# ============================================================
# 12. ACCRUE ANNUAL LEAVE FOR ONE EMPLOYEE
# ============================================================

def accrue_annual_leave_for_employee(
    db: Session,
    employee_id: int,
    as_of_date: date | None = None,
) -> dict:
    """
    Accrue annual leave for one employee.

    Handles:
        1. Employee validation.
        2. Previous service-year finalization.
        3. Current service-year monthly accrual.
        4. Balance initialization.
        5. Duplicate-credit protection.
        6. Positive accrual ledger transactions.
        7. Audit logging.
        8. Atomic database commit.

    Historical protection:
        Missing historical balances are not automatically created.

    Idempotency:
        Existing entitlement is compared with the calculated target.
        Only the additional amount is credited.

    Transaction management:
        Previous and current service-year updates are committed together.
    """

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    try:

        # ----------------------------------------------------
        # STEP 1: RETRIEVE AND VALIDATE EMPLOYEE
        # ----------------------------------------------------

        employee = get_employee_by_id(
            db,
            employee_id,
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        if not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot accrue leave for inactive employees",
            )

        if employee.hire_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee hire date is required",
            )

        if as_of_date < employee.hire_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Calculation date cannot precede hire date",
            )

        # ----------------------------------------------------
        # HELPER: APPLY ACCRUAL TO AN EXISTING BALANCE
        # ----------------------------------------------------

        def apply_accrual(
            leave_balance: LeaveBalance,
            calculated_target: Decimal,
            balance_year: int,
            service_period_start: date,
            service_period_end: date,
        ) -> dict:

            previous_entitlement = Decimal(
                str(leave_balance.entitlement_days)
            )

            used_days = Decimal(
                str(leave_balance.used_days)
            )

            # Never automatically reduce an existing entitlement.
            # This preserves additional contractual benefits
            # and previously consumed leave.

            effective_target = max(
                calculated_target,
                previous_entitlement,
                used_days,
            )

            additional_credit = (
                effective_target - previous_entitlement
            )

            if additional_credit > 0:

                leave_balance.entitlement_days = effective_target

                leave_balance.updated_at = datetime.now(
                    timezone.utc
                )

                # Create positive accrual transaction.

                create_leave_transaction(
                    db,
                    {
                        "employee_id": employee_id,
                        "leave_balance_id": (
                            leave_balance.leave_balance_id
                        ),
                        "leave_request_id": None,
                        "transaction_type": "accrual",
                        "days_delta": additional_credit,
                        "notes": (
                            f"Annual leave accrual for service year "
                            f"{balance_year}. "
                            f"Previous entitlement: "
                            f"{previous_entitlement}. "
                            f"Additional credit: {additional_credit}. "
                            f"New entitlement: {effective_target}. "
                            f"Calculation date: {as_of_date}."
                        ),
                        "actor_user_id": None,
                    },
                )

                # Record audit event.

                record_leave_audit(
                    db=db,
                    actor_user_id=None,
                    action="LEAVE_BALANCE_CREDITED",
                    entity_type="LeaveBalance",
                    entity_id=leave_balance.leave_balance_id,
                    details={
                        "employee_id": employee_id,
                        "leave_type": "annual",
                        "balance_year": balance_year,
                        "previous_entitlement": str(
                            previous_entitlement
                        ),
                        "additional_credit": str(
                            additional_credit
                        ),
                        "new_entitlement": str(
                            effective_target
                        ),
                        "as_of_date": as_of_date.isoformat(),
                    },
                )

            return {
                "balance_year": balance_year,
                "service_period_start": service_period_start,
                "service_period_end": service_period_end,
                "calculated_target": calculated_target,
                "previous_entitlement": previous_entitlement,
                "additional_credit": additional_credit,
                "entitlement_days": effective_target,
                "used_days": used_days,
                "available_days": effective_target - used_days,
            }

        # ----------------------------------------------------
        # STEP 2: IDENTIFY CURRENT SERVICE YEAR
        # ----------------------------------------------------

        current_period = get_employee_service_year_period(
            hire_date=employee.hire_date,
            reference_date=as_of_date,
        )

        current_service_year = current_period["service_year"]

        # ----------------------------------------------------
        # STEP 3: FINALIZE PREVIOUS SERVICE YEAR IF IT EXISTS
        # ----------------------------------------------------

        previous_service_year_result = None

        if current_service_year > 1:

            previous_period_start = _add_calendar_months(
                employee.hire_date,
                (current_service_year - 2) * 12,
            )

            previous_period_end = (
                current_period["start_date"]
                - timedelta(days=1)
            )

            previous_balance_year = previous_period_start.year

            # Retrieve only an existing historical balance.
            # Do not automatically initialize missing history.

            previous_balance = (
                get_employee_leave_balance_for_update(
                    db=db,
                    employee_id=employee_id,
                    leave_type="annual",
                    balance_year=previous_balance_year,
                )
            )

            if previous_balance is not None:

                previous_target = calculate_annual_leave_accrual_target(
                    hire_date=employee.hire_date,
                    balance_year=previous_balance_year,
                    as_of_date=as_of_date,
                )

                previous_service_year_result = apply_accrual(
                    leave_balance=previous_balance,
                    calculated_target=previous_target,
                    balance_year=previous_balance_year,
                    service_period_start=previous_period_start,
                    service_period_end=previous_period_end,
                )

            else:

                previous_service_year_result = {
                    "balance_year": previous_balance_year,
                    "status": "historical_balance_not_found",
                    "message": (
                        "Historical balance was not initialized. "
                        "No historical entitlement was created."
                    ),
                }

        # ----------------------------------------------------
        # STEP 4: CALCULATE CURRENT SERVICE-YEAR ENTITLEMENT
        # ----------------------------------------------------

        current_balance_year = current_period["balance_year"]

        current_target = calculate_annual_leave_accrual_target(
            hire_date=employee.hire_date,
            balance_year=current_balance_year,
            as_of_date=as_of_date,
        )

        # ----------------------------------------------------
        # STEP 5: CREATE OR RETRIEVE CURRENT BALANCE
        # ----------------------------------------------------

        current_balance = (
            get_or_create_employee_leave_balance_for_update(
                db=db,
                employee_id=employee_id,
                leave_type="annual",
                balance_year=current_balance_year,
            )
        )

        # ----------------------------------------------------
        # STEP 6: APPLY CURRENT SERVICE-YEAR ACCRUAL
        # ----------------------------------------------------

        current_accrual_result = apply_accrual(
            leave_balance=current_balance,
            calculated_target=current_target,
            balance_year=current_balance_year,
            service_period_start=current_period["start_date"],
            service_period_end=current_period["end_date"],
        )

        # ----------------------------------------------------
        # STEP 7: COMMIT ALL OPERATIONS ATOMICALLY
        # ----------------------------------------------------

        db.commit()

        db.refresh(current_balance)

        # ----------------------------------------------------
        # STEP 8: RETURN ACCRUAL SUMMARY
        # ----------------------------------------------------

        return {
            "employee_id": employee_id,
            "employee_code": employee.employee_code,
            "leave_type": "annual",

            "previous_service_year_finalization": (
                previous_service_year_result
            ),

            "current_service_year": current_accrual_result,

            "calculation_date": as_of_date,
        }

    except Exception:
        db.rollback()
        raise


# ============================================================
# 14. PREVIEW ANNUAL LEAVE ACCRUAL FOR ALL ACTIVE EMPLOYEES
# ============================================================

def preview_annual_leave_accrual_for_all_active_employees(
    db: Session,
    as_of_date: date | None = None,
    batch_size: int = 100,
) -> dict:
    """
    Generate a read-only preview of annual leave entitlement
    for all active employees.

    This function:
        1. Retrieves active employees in batches.
        2. Skips employees whose joining date is in the future.
        3. Calculates each employee's service-year entitlement.
        4. Retrieves any existing annual leave balance.
        5. Calculates the proposed additional credit.
        6. Calculates projected available balance.
        7. Reports employees requiring manual review.

    Database behaviour:
        READ ONLY.
        No balance creation.
        No ledger transactions.
        No audit inserts.
        No commits.
    """

    if batch_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size must be greater than zero",
        )

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    total_active_employees = 0
    employees_previewed = 0
    future_hires_skipped = 0
    missing_hire_dates_skipped = 0
    manual_review_required = 0

    total_proposed_credit = Decimal("0")

    employee_results = []
    skipped_employees = []

    offset = 0

    # Prevent queries from flushing unrelated pending ORM changes.
    with db.no_autoflush:

        # ----------------------------------------------------
        # STEP 1: RETRIEVE ACTIVE EMPLOYEES IN BATCHES
        # ----------------------------------------------------

        while True:

            employees, total_count = get_employees(
                db=db,
                is_active=True,
                skip=offset,
                limit=batch_size,
            )

            total_active_employees = total_count

            if not employees:
                break

            for employee in employees:

                # --------------------------------------------
                # STEP 2: VALIDATE HIRE DATE
                # --------------------------------------------

                if employee.hire_date is None:

                    missing_hire_dates_skipped += 1

                    skipped_employees.append({
                        "employee_id": employee.employee_id,
                        "employee_code": employee.employee_code,
                        "reason": "Missing hire date",
                    })

                    continue

                # --------------------------------------------
                # STEP 3: EXCLUDE FUTURE EMPLOYEES
                # --------------------------------------------

                if employee.hire_date > as_of_date:

                    future_hires_skipped += 1

                    skipped_employees.append({
                        "employee_id": employee.employee_id,
                        "employee_code": employee.employee_code,
                        "hire_date": employee.hire_date,
                        "reason": "Future joining date",
                    })

                    continue

                # --------------------------------------------
                # STEP 4: IDENTIFY SERVICE YEAR
                # --------------------------------------------

                service_period = get_employee_service_year_period(
                    hire_date=employee.hire_date,
                    reference_date=as_of_date,
                )

                balance_year = service_period["balance_year"]

                # --------------------------------------------
                # STEP 5: CALCULATE ENTITLEMENT TARGET
                # --------------------------------------------

                target_entitlement = (
                    calculate_annual_leave_accrual_target(
                        hire_date=employee.hire_date,
                        balance_year=balance_year,
                        as_of_date=as_of_date,
                    )
                )

                # --------------------------------------------
                # STEP 6: RETRIEVE EXISTING BALANCE
                # --------------------------------------------

                existing_balance = get_employee_leave_balance(
                    db=db,
                    employee_id=employee.employee_id,
                    leave_type="annual",
                    balance_year=balance_year,
                )

                if existing_balance is None:
                    existing_entitlement = Decimal("0")
                    used_days = Decimal("0")
                else:
                    existing_entitlement = Decimal(
                        str(existing_balance.entitlement_days)
                    )

                    used_days = Decimal(
                        str(existing_balance.used_days)
                    )

                # --------------------------------------------
                # STEP 7: CALCULATE PROPOSED CREDIT
                # --------------------------------------------

                additional_credit = max(
                    Decimal("0"),
                    target_entitlement - existing_entitlement,
                )

                # Preserve existing higher contractual
                # entitlement rather than reducing it.

                projected_entitlement = max(
                    target_entitlement,
                    existing_entitlement,
                    used_days,
                )

                projected_available = (
                    projected_entitlement - used_days
                )

                # --------------------------------------------
                # STEP 8: IDENTIFY RECONCILIATION WARNINGS
                # --------------------------------------------

                warnings = []

                if existing_entitlement > target_entitlement:
                    warnings.append(
                        "Existing entitlement exceeds calculated policy target"
                    )

                if used_days > target_entitlement:
                    warnings.append(
                        "Existing leave usage exceeds calculated policy target"
                    )

                if used_days > existing_entitlement:
                    warnings.append(
                        "Used days exceed existing credited entitlement"
                    )

                if warnings:
                    manual_review_required += 1

                # --------------------------------------------
                # STEP 9: BUILD EMPLOYEE PREVIEW
                # --------------------------------------------

                employees_previewed += 1

                total_proposed_credit += additional_credit

                employee_results.append({
                    "employee_id": employee.employee_id,
                    "employee_code": employee.employee_code,
                    "full_name": employee.full_name,
                    "hire_date": employee.hire_date,

                    "balance_year": balance_year,
                    "service_year_start": service_period["start_date"],
                    "service_year_end": service_period["end_date"],

                    "calculated_entitlement_days": target_entitlement,
                    "existing_entitlement_days": existing_entitlement,
                    "existing_used_days": used_days,

                    "proposed_additional_credit": additional_credit,
                    "projected_entitlement_days": projected_entitlement,
                    "projected_available_days": projected_available,

                    "requires_manual_review": bool(warnings),
                    "warnings": warnings,
                })

            offset += len(employees)

            if offset >= total_count:
                break

    # --------------------------------------------------------
    # STEP 10: RETURN READ-ONLY PREVIEW
    # --------------------------------------------------------

    return {
        "calculation_date": as_of_date,
        "total_active_employees": total_active_employees,
        "employees_previewed": employees_previewed,
        "future_hires_skipped": future_hires_skipped,
        "missing_hire_dates_skipped": missing_hire_dates_skipped,
        "manual_review_required": manual_review_required,
        "total_proposed_credit_days": total_proposed_credit,
        "employee_results": employee_results,
        "skipped_employees": skipped_employees,
        "database_modified": False,
    }


# ============================================================
# 13. BULK ANNUAL LEAVE ACCRUAL
# ============================================================

def accrue_annual_leave_for_all_active_employees(
    db: Session,
    as_of_date: date | None = None,
    batch_size: int = 100,
) -> dict:
    """
    Process annual leave accrual for all active employees.

    Each employee is processed independently.

    Future employees and employees without hire dates
    are skipped.

    Successful employee transactions are committed
    independently by accrue_annual_leave_for_employee().
    """

    if batch_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size must be greater than zero",
        )

    if as_of_date is None:
        as_of_date = datetime.now(
            ZoneInfo("Asia/Dubai")
        ).date()

    total_processed = 0
    total_failed = 0
    future_hires_skipped = 0
    missing_hire_dates_skipped = 0

    employee_results = []
    employee_errors = []
    skipped_employees = []

    offset = 0
    total_active_employees = 0

    while True:

        employees, total_count = get_employees(
            db=db,
            is_active=True,
            skip=offset,
            limit=batch_size,
        )

        total_active_employees = total_count

        if not employees:
            break

        # Capture employee details before individual commits.
        employee_records = [
            {
                "employee_id": employee.employee_id,
                "employee_code": employee.employee_code,
                "hire_date": employee.hire_date,
            }
            for employee in employees
        ]

        for employee in employee_records:

            employee_id = employee["employee_id"]
            hire_date = employee["hire_date"]

            # Skip missing joining dates.

            if hire_date is None:
                missing_hire_dates_skipped += 1

                skipped_employees.append({
                    "employee_id": employee_id,
                    "employee_code": employee["employee_code"],
                    "reason": "Missing hire date",
                })

                continue

            # Skip future employees.

            if hire_date > as_of_date:
                future_hires_skipped += 1

                skipped_employees.append({
                    "employee_id": employee_id,
                    "employee_code": employee["employee_code"],
                    "hire_date": hire_date,
                    "reason": "Future joining date",
                })

                continue

            # Process one eligible employee.

            try:

                result = accrue_annual_leave_for_employee(
                    db=db,
                    employee_id=employee_id,
                    as_of_date=as_of_date,
                )

                total_processed += 1
                employee_results.append(result)

            except Exception as exc:

                db.rollback()

                total_failed += 1

                employee_errors.append({
                    "employee_id": employee_id,
                    "employee_code": employee["employee_code"],
                    "error": str(exc),
                })

        offset += len(employee_records)

        if offset >= total_count:
            break

    return {
        "as_of_date": as_of_date,
        "total_active_employees": total_active_employees,
        "total_processed": total_processed,
        "total_failed": total_failed,
        "future_hires_skipped": future_hires_skipped,
        "missing_hire_dates_skipped": missing_hire_dates_skipped,
        "total_skipped": (
            future_hires_skipped
            + missing_hire_dates_skipped
        ),
        "employee_results": employee_results,
        "employee_errors": employee_errors,
        "skipped_employees": skipped_employees,
    }

# ============================================================
# 15. GET AUTHORIZED EMPLOYEE LEAVE BALANCES
# ============================================================

def get_leave_balances_for_user(
    db: Session,
    current_user: User,
    employee_id: int | None = None,
    balance_year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[LeaveBalance]:
    """
    Retrieve leave balances within the authenticated
    user's employee visibility scope.

    Access rules:
        Admin / HR:
            All employees.

        Manager:
            Own balances and direct reports.

        Employee:
            Own balances only.

    Optional filters:
        employee_id:
            Restrict results to a specific authorized employee.

        balance_year:
            Restrict results to a specific service year.

    Pagination:
        Applied to authorized employee records before
        retrieving their leave balances.

    Security:
        Employee visibility is enforced before balances
        are retrieved from the repository.
    """

    # STEP 1: Validate pagination.

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    # STEP 2: Determine authorized employee visibility.

    visibility_scope = get_employee_visibility_scope(
        current_user
    )

    own_employee_id = visibility_scope.get(
        "employee_id"
    )

    reporting_scope_manager_id = visibility_scope.get(
        "reporting_scope_manager_id"
    )

    # STEP 3: Prevent access outside employee scope.

    if (
        own_employee_id is not None
        and employee_id is not None
        and employee_id != own_employee_id
    ):
        return []

    target_employee_id = (
        employee_id
        if employee_id is not None
        else own_employee_id
    )

    # STEP 4: Retrieve only authorized employees.

    authorized_employees, _ = get_employees(
        db=db,
        employee_id=target_employee_id,
        reporting_scope_manager_id=(
            reporting_scope_manager_id
        ),
        skip=skip,
        limit=limit,
    )

    authorized_employee_ids = [
        employee.employee_id
        for employee in authorized_employees
    ]

    # STEP 5: Retrieve balances for authorized employees.

    return get_leave_balances_for_employees(
        db=db,
        employee_ids=authorized_employee_ids,
        balance_year=balance_year,
    )

# ============================================================
# 16. GET AUTHORIZED LEAVE TRANSACTION HISTORY
# ============================================================

def get_leave_transactions_for_user(
    db: Session,
    current_user: User,
    employee_id: int | None = None,
    transaction_type: str | None = None,
    leave_type: str | None = None,
    balance_year: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[LeaveTransaction]:
    """
    Retrieve leave transaction history within the
    authenticated user's employee visibility scope.

    Access:
        Admin / HR:
            All employees.

        Manager:
            Own transactions and direct reports.

        Employee:
            Own transactions only.

    Filters:
        employee_id
        transaction_type
        leave_type
        balance_year

    Pagination:
        skip and limit apply to transaction records.

    Security:
        Employee visibility is enforced before retrieving
        transaction records.

    Database:
        Read-only operation. No commits or modifications.
    """

    # STEP 1: Validate pagination.

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters",
        )

    # STEP 2: Determine authorized visibility.

    visibility_scope = get_employee_visibility_scope(
        current_user
    )

    own_employee_id = visibility_scope.get(
        "employee_id"
    )

    reporting_scope_manager_id = visibility_scope.get(
        "reporting_scope_manager_id"
    )

    # STEP 3: Prevent employees accessing other employees.

    if (
        own_employee_id is not None
        and employee_id is not None
        and employee_id != own_employee_id
    ):
        return []

    target_employee_id = (
        employee_id
        if employee_id is not None
        else own_employee_id
    )

    # STEP 4: Retrieve all authorized employee IDs.
    # Use batches so larger organizations are supported.

    authorized_employee_ids = []

    employee_offset = 0
    employee_batch_size = 500

    while True:

        employees, total_count = get_employees(
            db=db,
            employee_id=target_employee_id,
            reporting_scope_manager_id=(
                reporting_scope_manager_id
            ),
            skip=employee_offset,
            limit=employee_batch_size,
        )

        if not employees:
            break

        authorized_employee_ids.extend(
            employee.employee_id
            for employee in employees
        )

        employee_offset += len(employees)

        if employee_offset >= total_count:
            break

    # STEP 5: Retrieve authorized transaction history.

    return get_leave_transactions_for_employees(
        db=db,
        employee_ids=authorized_employee_ids,
        transaction_type=transaction_type,
        leave_type=leave_type,
        balance_year=balance_year,
        skip=skip,
        limit=limit,
    )
