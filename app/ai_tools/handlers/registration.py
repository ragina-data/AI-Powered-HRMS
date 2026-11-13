
from app.ai_tools.registry import tool_registry

from app.ai_tools.handlers.employee_handlers import (
    get_my_employee_profile,
    get_authorized_employee_profile,
    search_authorized_employees,
)

from app.ai_tools.handlers.leave_handlers import (
    get_my_leave_requests,
    get_my_leave_balance,
    get_authorized_leave_balances,
    get_my_leave_transactions,
    get_authorized_leave_transactions,
    submit_leave_request_handler,
    decide_leave_request_handler,
)

from app.ai_tools.handlers.document_handlers import (
    list_available_document_types,
    submit_document_request_handler,
    get_my_document_requests,
    get_authorized_document_requests,
    process_document_request_handler,
    get_my_document_request_history,
    get_authorized_document_request_history,
)

def register_employee_handlers() -> None:
    tool_registry.register_handler(
        "get_my_employee_profile",
        get_my_employee_profile,
    )

    tool_registry.register_handler(
        "get_authorized_employee_profile",
        get_authorized_employee_profile,
    )

    tool_registry.register_handler(
        "search_authorized_employees",
        search_authorized_employees,
    )

def register_leave_handlers() -> None:
    tool_registry.register_handler(
        "get_my_leave_requests",
        get_my_leave_requests,
    )
    tool_registry.register_handler(
        "get_my_leave_balance",
        get_my_leave_balance,
    )
    tool_registry.register_handler(
        "get_authorized_leave_balances",
        get_authorized_leave_balances,
    )
    tool_registry.register_handler(
        "get_my_leave_transactions",
        get_my_leave_transactions,
    )
    tool_registry.register_handler(
        "get_authorized_leave_transactions",
        get_authorized_leave_transactions,
    )
    tool_registry.register_handler(
        "submit_leave_request",
        submit_leave_request_handler,
    )
    tool_registry.register_handler(
        "decide_leave_request",
        decide_leave_request_handler,
    )
def register_document_handlers() -> None:
    tool_registry.register_handler(
        "list_available_document_types",
        list_available_document_types,
    )

    tool_registry.register_handler(
        "submit_document_request",
        submit_document_request_handler,
    )

    tool_registry.register_handler(
        "get_my_document_requests",
        get_my_document_requests,
    )

    tool_registry.register_handler(
        "get_authorized_document_requests",
        get_authorized_document_requests,
    )

    tool_registry.register_handler(
        "process_document_request",
        process_document_request_handler,
    )

    tool_registry.register_handler(
        "get_my_document_request_history",
        get_my_document_request_history,
    )

    tool_registry.register_handler(
        "get_authorized_document_request_history",
        get_authorized_document_request_history,
    )

def register_all_handlers() -> None:
    """Register all AI tool handlers once."""

    if not tool_registry.is_executable("get_my_employee_profile"):
        register_employee_handlers()

    if not tool_registry.is_executable("get_my_leave_requests"):
        register_leave_handlers()

    if not tool_registry.is_executable("list_available_document_types"):
        register_document_handlers()
