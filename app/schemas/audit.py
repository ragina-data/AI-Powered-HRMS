from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_log_id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime