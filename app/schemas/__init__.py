from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)

from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveApprovalCreate,
    LeaveBalanceResponse,
)

from app.schemas.document import (
    DocumentRequestCreate,
    DocumentRequestResponse,
    DocumentProcessRequest,
    DocumentRequestHistoryResponse,
)

from app.schemas.timesheet import (
    TimesheetEntryCreate,
    TimesheetCreate,
    TimesheetEntryResponse,
    TimesheetResponse,
    TimesheetApprovalCreate,
)

from app.schemas.ai_assistant import (
    AIConversationCreate,
    AIConversationResponse,
    AIMessageCreate,
    AIMessageResponse,
)

from app.schemas.audit import (
    AuditLogResponse,
)