
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

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
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
