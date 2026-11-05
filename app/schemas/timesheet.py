
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------
# TIMESHEET ENTRY CREATE
# --------------------------------------------------

class TimesheetEntryCreate(BaseModel):
    work_date: date

    hours_worked: Decimal = Field(
        gt=0,
        le=24,
        max_digits=5,
        decimal_places=2
    )

    task_description: str | None = Field(
        default=None,
        max_length=2000
    )

    project_code: str | None = Field(
        default=None,
        max_length=100
    )


# --------------------------------------------------
# TIMESHEET CREATE
# --------------------------------------------------

class TimesheetCreate(BaseModel):
    period_start: date
    period_end: date

    entries: list[TimesheetEntryCreate] = Field(
        min_length=1
    )

    comments: str | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("Period end cannot be before period start.")

        for entry in self.entries:
            if not self.period_start <= entry.work_date <= self.period_end:
                raise ValueError(
                    "Every timesheet entry must fall within the timesheet period."
                )

        return self


# --------------------------------------------------
# TIMESHEET ENTRY RESPONSE
# --------------------------------------------------

class TimesheetEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_entry_id: int
    timesheet_id: int
    work_date: date
    hours_worked: Decimal
    task_description: str | None
    project_code: str | None


# --------------------------------------------------
# TIMESHEET RESPONSE
# --------------------------------------------------

class TimesheetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timesheet_id: int
    employee_id: int
    period_start: date
    period_end: date
    status: str
    submitted_at: datetime | None
    approved_at: datetime | None
    total_hours: Decimal
    comments: str | None
    entries: list[TimesheetEntryResponse] = Field(
        default_factory=list
    )


# --------------------------------------------------
# TIMESHEET APPROVAL
# --------------------------------------------------

class TimesheetApprovalCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str | None = Field(
        default=None,
        max_length=2000
    )
