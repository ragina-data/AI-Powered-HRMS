
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# DEPARTMENT CREATE
# --------------------------------------------------

class DepartmentCreate(BaseModel):
    department_name: str = Field(
        min_length=2,
        max_length=100
    )

    department_code: str | None = Field(
        default=None,
        max_length=30
    )

    parent_department_id: int | None = Field(
        default=None,
        gt=0
    )


# --------------------------------------------------
# DEPARTMENT UPDATE
# --------------------------------------------------

class DepartmentUpdate(BaseModel):
    department_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    department_code: str | None = Field(
        default=None,
        max_length=30
    )

    parent_department_id: int | None = Field(
        default=None,
        gt=0
    )

    is_active: bool | None = None


# --------------------------------------------------
# DEPARTMENT RESPONSE
# --------------------------------------------------

class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_id: int
    department_name: str
    department_code: str | None
    parent_department_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
