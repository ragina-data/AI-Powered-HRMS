
"""
HRMS AI Agent Tool Definitions
==============================

Purpose:
    Define all supported HRMS operations available to Gemini.

Categories:
    1. Employee Management
    2. Leave Management
    3. Document Management
    4. HR Policy Knowledge (future RAG integration)

Security:
    1. Every tool declares its required RBAC permissions.
    2. Employee identity is derived from authenticated context.
    3. Sensitive operations require explicit confirmation.
    4. Gemini cannot execute arbitrary SQL.
    5. Only tools with implemented handlers are exposed to Gemini.
"""

from dataclasses import dataclass
from typing import Any, Literal


# ============================================================
# TOOL DEFINITION
# ============================================================

@dataclass(frozen=True)
class ToolDefinition:

    name: str
    description: str

    parameters: dict[str, Any]

    required_permissions: tuple[str, ...]

    category: str

    operation_type: Literal["read", "write"]

    requires_confirmation: bool = False


# ============================================================
# COMMON JSON SCHEMAS
# ============================================================

NO_ARGUMENTS = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


# ============================================================
# 1. EMPLOYEE MANAGEMENT TOOLS
# ============================================================

GET_MY_EMPLOYEE_PROFILE = ToolDefinition(
    name="get_my_employee_profile",
    description=(
        "Retrieve the authenticated employee's own HRMS "
        "profile and employment information."
    ),
    parameters=NO_ARGUMENTS,
    required_permissions=("employee.read_self",),
    category="employee",
    operation_type="read",
)


GET_AUTHORIZED_EMPLOYEE_PROFILE = ToolDefinition(
    name="get_authorized_employee_profile",
    description=(
        "Retrieve an employee profile only when the "
        "authenticated user is authorized to access it."
    ),
    parameters={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "integer",
                "minimum": 1,
                "description": "Target employee ID.",
            },
        },
        "required": ["employee_id"],
        "additionalProperties": False,
    },
    required_permissions=("employee.read_team",),
    category="employee",
    operation_type="read",
)


SEARCH_AUTHORIZED_EMPLOYEES = ToolDefinition(
    name="search_authorized_employees",
    description=(
        "Search employees within the authenticated user's "
        "authorized employee visibility scope."
    ),
    parameters={
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "maxLength": 150,
            },
            "department_id": {
                "type": "integer",
                "minimum": 1,
            },
            "manager_employee_id": {
                "type": "integer",
                "minimum": 1,
            },
            "is_active": {
                "type": "boolean",
            },
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("employee.read_team",),
    category="employee",
    operation_type="read",
)


# ============================================================
# 2. LEAVE MANAGEMENT TOOLS
# ============================================================

GET_MY_LEAVE_REQUESTS = ToolDefinition(
    name="get_my_leave_requests",
    description=(
        "Retrieve the authenticated employee's own leave "
        "applications and their approval statuses."
    ),
    parameters={
        "type": "object",
        "properties": {
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("leave.read_self",),
    category="leave",
    operation_type="read",
)


GET_MY_LEAVE_BALANCE = ToolDefinition(
    name="get_my_leave_balance",
    description=(
        "Retrieve the authenticated employee's own leave "
        "balances for a specified year."
    ),
    parameters={
        "type": "object",
        "properties": {
            "balance_year": {
                "type": "integer",
                "minimum": 2000,
                "maximum": 2100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("leave.read_self",),
    category="leave",
    operation_type="read",
)


GET_AUTHORIZED_LEAVE_BALANCES = ToolDefinition(
    name="get_authorized_leave_balances",
    description=(
        "Retrieve leave balances within the authenticated "
        "manager's team or HR/Admin organization-wide scope."
    ),
    parameters={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "integer",
                "minimum": 1,
                "description": "Optional employee filter.",
            },
            "balance_year": {
                "type": "integer",
                "minimum": 2000,
                "maximum": 2100,
            },
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=(
        "employee.read_team",
        "leave.manage_all",
    ),
    category="leave",
    operation_type="read",
)


GET_MY_LEAVE_TRANSACTIONS = ToolDefinition(
    name="get_my_leave_transactions",
    description=(
        "Retrieve the authenticated employee's own leave "
        "accruals, deductions and adjustments."
    ),
    parameters={
        "type": "object",
        "properties": {
            "transaction_type": {
                "type": "string",
                "maxLength": 20,
            },
            "leave_type": {
                "type": "string",
                "maxLength": 30,
            },
            "balance_year": {
                "type": "integer",
                "minimum": 1,
            },
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("leave.read_self",),
    category="leave",
    operation_type="read",
)


GET_AUTHORIZED_LEAVE_TRANSACTIONS = ToolDefinition(
    name="get_authorized_leave_transactions",
    description=(
        "Retrieve leave transactions belonging to employees "
        "within the authenticated user's visibility scope."
    ),
    parameters={
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "integer",
                "minimum": 1,
            },
            "transaction_type": {
                "type": "string",
                "maxLength": 20,
            },
            "leave_type": {
                "type": "string",
                "maxLength": 30,
            },
            "balance_year": {
                "type": "integer",
                "minimum": 1,
            },
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=(
        "leave.approve_team",
        "leave.manage_all",
    ),
    category="leave",
    operation_type="read",
)


SUBMIT_LEAVE_REQUEST = ToolDefinition(
    name="submit_leave_request",
    description=(
        "Submit a new leave application for the authenticated "
        "employee. The HRMS validates eligibility, dates and "
        "leave balance. A successful request starts as pending."
    ),
    parameters={
        "type": "object",
        "properties": {
            "leave_type": {
                "type": "string",
                "maxLength": 30,
            },
            "start_date": {
                "type": "string",
                "format": "date",
            },
            "end_date": {
                "type": "string",
                "format": "date",
            },
            "reason": {
                "type": ["string", "null"],
            },
            "medical_certificate_submitted": {
                "type": "boolean",
            },
        },
        "required": [
            "leave_type",
            "start_date",
            "end_date",
        ],
        "additionalProperties": False,
    },
    required_permissions=("leave.request",),
    category="leave",
    operation_type="write",
    requires_confirmation=True,
)


DECIDE_LEAVE_REQUEST = ToolDefinition(
    name="decide_leave_request",
    description=(
        "Approve or reject a pending leave request. "
        "The backend validates the approver's authorization, "
        "reporting scope and available leave balance."
    ),
    parameters={
        "type": "object",
        "properties": {
            "leave_request_id": {
                "type": "integer",
                "minimum": 1,
            },
            "decision": {
                "type": "string",
                "enum": ["approved", "rejected"],
            },
            "comments": {
                "type": ["string", "null"],
            },
        },
        "required": [
            "leave_request_id",
            "decision",
        ],
        "additionalProperties": False,
    },
    required_permissions=(
        "leave.approve_team",
        "leave.manage_all",
    ),
    category="leave",
    operation_type="write",
    requires_confirmation=True,
)


# ============================================================
# 3. DOCUMENT MANAGEMENT TOOLS
# ============================================================

LIST_AVAILABLE_DOCUMENT_TYPES = ToolDefinition(
    name="list_available_document_types",
    description=(
        "Retrieve active HR document types available "
        "for employee requests."
    ),
    parameters=NO_ARGUMENTS,
    required_permissions=("document.request",),
    category="document",
    operation_type="read",
)


SUBMIT_DOCUMENT_REQUEST = ToolDefinition(
    name="submit_document_request",
    description=(
        "Submit an HR document request for the authenticated "
        "employee using an active document type."
    ),
    parameters={
        "type": "object",
        "properties": {
            "document_type": {
                "type": "string",
                "maxLength": 50,
            },
            "purpose": {
                "type": ["string", "null"],
                "maxLength": 2000,
            },
        },
        "required": ["document_type"],
        "additionalProperties": False,
    },
    required_permissions=("document.request",),
    category="document",
    operation_type="write",
    requires_confirmation=True,
)


GET_MY_DOCUMENT_REQUESTS = ToolDefinition(
    name="get_my_document_requests",
    description=(
        "Retrieve the authenticated employee's own HR "
        "document requests and their statuses."
    ),
    parameters={
        "type": "object",
        "properties": {
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("document.read_self",),
    category="document",
    operation_type="read",
)


GET_AUTHORIZED_DOCUMENT_REQUESTS = ToolDefinition(
    name="get_authorized_document_requests",
    description=(
        "Retrieve organization-wide HR document requests "
        "for authorized HR and Admin users. Supports "
        "status, employee and document type filters."
    ),
    parameters={
        "type": "object",
        "properties": {
            "request_status": {
                "type": "string",
                "enum": [
                    "pending",
                    "approved",
                    "processing",
                    "completed",
                    "rejected",
                    "cancelled",
                ],
            },
            "employee_id": {
                "type": "integer",
                "minimum": 1,
            },
            "document_type": {
                "type": "string",
                "maxLength": 50,
            },
            "skip": {
                "type": "integer",
                "minimum": 0,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "additionalProperties": False,
    },
    required_permissions=("document.process",),
    category="document",
    operation_type="read",
)


PROCESS_DOCUMENT_REQUEST = ToolDefinition(
    name="process_document_request",
    description=(
        "Move an HR document request through an allowed "
        "workflow status. Supported target statuses are "
        "approved, processing, rejected and completed. "
        "The backend validates the current status and "
        "permitted transition."
    ),
    parameters={
        "type": "object",
        "properties": {
            "document_request_id": {
                "type": "integer",
                "minimum": 1,
            },
            "status": {
                "type": "string",
                "enum": [
                    "approved",
                    "processing",
                    "rejected",
                    "completed",
                ],
            },
            "remarks": {
                "type": ["string", "null"],
                "maxLength": 2000,
            },
            "document_reference": {
                "type": ["string", "null"],
                "maxLength": 255,
            },
        },
        "required": [
            "document_request_id",
            "status",
        ],
        "additionalProperties": False,
    },
    required_permissions=("document.process",),
    category="document",
    operation_type="write",
    requires_confirmation=True,
)


GET_MY_DOCUMENT_REQUEST_HISTORY = ToolDefinition(
    name="get_my_document_request_history",
    description=(
        "Retrieve the chronological history of the "
        "authenticated employee's own document request."
    ),
    parameters={
        "type": "object",
        "properties": {
            "document_request_id": {
                "type": "integer",
                "minimum": 1,
            },
        },
        "required": ["document_request_id"],
        "additionalProperties": False,
    },
    required_permissions=("document.read_self",),
    category="document",
    operation_type="read",
)


GET_AUTHORIZED_DOCUMENT_REQUEST_HISTORY = ToolDefinition(
    name="get_authorized_document_request_history",
    description=(
        "Retrieve document request history for an authorized "
        "HR or Admin user."
    ),
    parameters={
        "type": "object",
        "properties": {
            "document_request_id": {
                "type": "integer",
                "minimum": 1,
            },
        },
        "required": ["document_request_id"],
        "additionalProperties": False,
    },
    required_permissions=("document.process",),
    category="document",
    operation_type="read",
)


# ============================================================
# CENTRAL TOOL CATALOGUE
# ============================================================

TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    tool.name: tool
    for tool in [
        GET_MY_EMPLOYEE_PROFILE,
        GET_AUTHORIZED_EMPLOYEE_PROFILE,
        SEARCH_AUTHORIZED_EMPLOYEES,

        GET_MY_LEAVE_REQUESTS,
        GET_MY_LEAVE_BALANCE,
        GET_AUTHORIZED_LEAVE_BALANCES,
        GET_MY_LEAVE_TRANSACTIONS,
        GET_AUTHORIZED_LEAVE_TRANSACTIONS,
        SUBMIT_LEAVE_REQUEST,
        DECIDE_LEAVE_REQUEST,

        LIST_AVAILABLE_DOCUMENT_TYPES,
        SUBMIT_DOCUMENT_REQUEST,
        GET_MY_DOCUMENT_REQUESTS,
        GET_AUTHORIZED_DOCUMENT_REQUESTS,
        PROCESS_DOCUMENT_REQUEST,
        GET_MY_DOCUMENT_REQUEST_HISTORY,
        GET_AUTHORIZED_DOCUMENT_REQUEST_HISTORY,
    ]
}


# ============================================================
# TOOL LOOKUP
# ============================================================

def get_tool_definition(
    tool_name: str,
) -> ToolDefinition | None:

    return TOOL_DEFINITIONS.get(tool_name)


# ============================================================
# LIST TOOL DEFINITIONS
# ============================================================

def get_all_tool_definitions() -> list[ToolDefinition]:

    return list(TOOL_DEFINITIONS.values())


# ============================================================
# LIST TOOLS BY CATEGORY
# ============================================================

def get_tools_by_category(
    category: str,
) -> list[ToolDefinition]:

    return [
        tool
        for tool in TOOL_DEFINITIONS.values()
        if tool.category == category
    ]


# ============================================================
# LIST ACTION TOOLS REQUIRING CONFIRMATION
# ============================================================

def get_confirmation_required_tools() -> list[ToolDefinition]:

    return [
        tool
        for tool in TOOL_DEFINITIONS.values()
        if tool.requires_confirmation
    ]
