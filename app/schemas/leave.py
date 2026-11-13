
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------
# LEAVE REQUEST CREATE
# --------------------------------------------------

class LeaveRequestCreate(BaseModel):
    leave_type: str = Field(min_length=1, max_length=30)
    start_date: date
    end_date: date
    reason: str | None = None

    medical_certificate_submitted: bool = Field(
        default=False,
        description="Whether the employee has submitted a medical certificate",
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
        return self

    @model_validator(mode="after")
    def validate_medical_certificate(self):
        if (
            self.medical_certificate_submitted
            and self.leave_type.strip().lower() != "sick"
        ):
            raise ValueError(
                "Medical certificate submission applies only to sick leave."
            )
        return self


# --------------------------------------------------
# LEAVE REQUEST RESPONSE
# --------------------------------------------------

class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_request_id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days_requested: Decimal
    reason: str | None
    medical_certificate_submitted: bool
    status: str
    submitted_at: datetime
    updated_at: datetime


# --------------------------------------------------
# LEAVE APPROVAL
# --------------------------------------------------

class LeaveApprovalCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str | None = None


# --------------------------------------------------
# LEAVE BALANCE RESPONSE
# --------------------------------------------------

class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_balance_id: int
    employee_id: int
    leave_type: str
    entitlement_days: Decimal
    used_days: Decimal
    balance_year: int


# --------------------------------------------------
# LEAVE TRANSACTION RESPONSE
# --------------------------------------------------

class LeaveTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_transaction_id: int
    employee_id: int
    leave_balance_id: int
    leave_request_id: int | None = None

    transaction_type: str
    days_delta: Decimal

    notes: str | None = None
    actor_user_id: int | None = None

    created_at: datetime

# --------------------------------------------------
# LEAVE DECISION RESPONSE
# --------------------------------------------------

class LeaveDecisionResponse(BaseModel):
    leave_request_id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days_requested: Decimal
    reason: str | None
    sick_leave_pay_breakdown: list[dict] = Field(
        default_factory=list
    )
    medical_certificate_submitted: bool = False
    status: Literal["approved", "rejected"]
    approval_id: int
    approver_employee_id: int
    balance_deductions: list[dict] = Field(
        default_factory=list
    )
class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_balance_id: int
    employee_id: int
    leave_type: str
    entitlement_days: Decimal
    used_days: Decimal
    available_days: Decimal
    balance_year: int