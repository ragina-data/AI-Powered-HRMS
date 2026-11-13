
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------
# DOCUMENT REQUEST CREATE
# --------------------------------------------------

class DocumentRequestCreate(BaseModel):
    document_type: str = Field(
        min_length=1,
        max_length=50
    )

    purpose: str | None = Field(
        default=None,
        max_length=2000
    )

# --------------------------------------------------
# DOCUMENT TYPE RESPONSE
# --------------------------------------------------

class DocumentTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_type_id: int
    document_type_code: str
    document_type_name: str
    description: str | None
    requires_hr_approval: bool
    is_active: bool
# --------------------------------------------------
# DOCUMENT REQUEST RESPONSE
# --------------------------------------------------

class DocumentRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_request_id: int
    employee_id: int
    document_type: str
    purpose: str | None
    status: str
    requested_at: datetime
    processed_by_employee_id: int | None
    processed_at: datetime | None
    remarks: str | None
    document_reference: str | None


# --------------------------------------------------
# DOCUMENT PROCESSING
# --------------------------------------------------

class DocumentProcessRequest(BaseModel):
    status: str = Field(
    pattern="^(approved|processing|rejected|completed)$",
    description=(
        "approved: HR approved the request. "
        "processing: Document preparation is underway. "
        "completed: Document has been issued. "
        "rejected: HR rejected the request."
    ),
)

    remarks: str | None = Field(
        default=None,
        max_length=2000
    )

    document_reference: str | None = Field(
        default=None,
        max_length=255
    )


# --------------------------------------------------
# DOCUMENT REQUEST HISTORY
# --------------------------------------------------

class DocumentRequestHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    document_request_id: int
    previous_status: str | None
    new_status: str
    action_by_user_id: int | None
    comments: str | None
    action_at: datetime
