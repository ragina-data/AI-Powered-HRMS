
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


# --------------------------------------------------
# EMPLOYEE CREATE
# --------------------------------------------------

class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    department_id: int = Field(gt=0)
    job_title: str = Field(min_length=2, max_length=100)
    hire_date: date
    manager_employee_id: int | None = Field(default=None, gt=0)


# --------------------------------------------------
# EMPLOYEE UPDATE
# --------------------------------------------------

class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    department_id: int | None = Field(default=None, gt=0)
    job_title: str | None = Field(default=None, min_length=2, max_length=100)
    hire_date: date | None = None
    manager_employee_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    @model_validator(mode="after")
    def validate_required_fields(self):
        if (
            "full_name" in self.model_fields_set
            and self.full_name is None
        ):
            raise ValueError("Full name cannot be null")

        if (
            "email" in self.model_fields_set
            and self.email is None
        ):
            raise ValueError("Email cannot be null")

        return self

# --------------------------------------------------
# EMPLOYEE RESPONSE
# --------------------------------------------------

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    employee_code: str
    full_name: str
    email: str
    department: str | None = Field(
    default=None,
    validation_alias="department_display",
    )
    department_id: int | None
    job_title: str | None
    hire_date: date | None
    manager_employee_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

# --------------------------------------------------
# EMPLOYEE LIST RESPONSE
# --------------------------------------------------

class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]

    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(gt=0

)

# --------------------------------------------------
# EMPLOYEE STATUS UPDATE
# --------------------------------------------------

class EmployeeStatusUpdate(BaseModel):
    is_active: bool