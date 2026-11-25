
"""
AI Tool Executor
================

Purpose:
    Securely execute registered HRMS AI tools.

Responsibilities:
    1. Validate tool arguments.
    2. Verify conversation ownership.
    3. Enforce user permissions.
    4. Execute authorized read operations.
    5. Require confirmation before write operations.
    6. Record tool execution audit history.
"""

import logging

from datetime import datetime, timezone
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy.orm import Session

from app.api.permissions import user_has_permission
from app.ai_tools.registry import tool_registry
from app.models.ai_conversation import AIConversation
from app.models.ai_tool_execution import AIToolExecution
from app.models.user import User


logger = logging.getLogger(__name__)


# ============================================================
# EXECUTOR EXCEPTIONS
# ============================================================

class ToolExecutionError(Exception):
    """Base exception for AI tool execution."""


class ToolArgumentValidationError(ToolExecutionError):
    """Raised when tool arguments are invalid."""


class ToolPermissionError(ToolExecutionError):
    """Raised when the user lacks the required permission."""


class ToolConversationAccessError(ToolExecutionError):
    """Raised when the conversation is inaccessible."""


class ToolExecutionNotFoundError(ToolExecutionError):
    """Raised when a tool execution record cannot be found."""


class ToolConfirmationError(ToolExecutionError):
    """Raised when a tool execution cannot be confirmed."""


# ============================================================
# ARGUMENT VALIDATION
# ============================================================

def validate_tool_arguments(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate Gemini-provided arguments against the registered
    JSON Schema.

    Backend dependencies such as db and current_user are never
    accepted from Gemini.
    """

    if not isinstance(arguments, dict):
        raise ToolArgumentValidationError(
            "Tool arguments must be a JSON object."
        )

    try:
        definition = tool_registry.get_definition(tool_name)

    except Exception as exc:
        raise ToolArgumentValidationError(
            f"Unknown AI tool: {tool_name}"
        ) from exc

    validator = Draft202012Validator(
        definition.parameters,
        format_checker=FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(arguments),
        key=lambda error: list(error.path),
    )

    if errors:
        error_messages = [
            f"{'.'.join(str(part) for part in error.path) or 'arguments'}: "
            f"{error.message}"
            for error in errors
        ]

        raise ToolArgumentValidationError(
            "; ".join(error_messages)
        )

    return arguments


# ============================================================
# CONVERSATION OWNERSHIP
# ============================================================

def verify_conversation_access(
    db: Session,
    conversation_id: int,
    current_user: User,
) -> AIConversation:
    """
    Ensure the authenticated user owns an active conversation.
    """

    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.conversation_id == conversation_id,
            AIConversation.user_id == current_user.user_id,
            AIConversation.status == "active",
        )
        .first()
    )

    if conversation is None:
        raise ToolConversationAccessError(
            "Conversation not found or is not accessible."
        )

    return conversation


# ============================================================
# PERMISSION ENFORCEMENT
# ============================================================


def verify_tool_permission(
    db: Session,
    current_user: User,
    tool_name: str,
) -> None:
    """
    Check whether the authenticated user has at least one
    permission required by the tool.

    Multiple permissions use OR semantics.
    """

    definition = tool_registry.get_definition(tool_name)

    if not definition.required_permissions:
        raise ToolPermissionError(
            "This tool has no configured permissions."
        )

    has_permission = any(
        user_has_permission(
            db=db,
            user_id=current_user.user_id,
            permission_code=permission_code,
        )
        for permission_code in definition.required_permissions
    )

    if not has_permission:
        raise ToolPermissionError(
            "You do not have permission to use this HRMS operation."
        )


# ============================================================
# AUDIT RECORD CREATION
# ============================================================

def create_tool_execution_record(
    db: Session,
    conversation_id: int,
    current_user: User,
    tool_name: str,
    arguments: dict[str, Any],
    message_id: int | None = None,
    execution_status: str = "started",
) -> AIToolExecution:
    """
    Create an audit record for an AI tool execution.
    """

    execution = AIToolExecution(
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=current_user.user_id,
        tool_name=tool_name,
        input_arguments=arguments,
        execution_status=execution_status,
    )

    db.add(execution)
    db.flush()

    return execution


# ============================================================
# AUDIT RECORD COMPLETION
# ============================================================

def complete_tool_execution(
    db: Session,
    execution: AIToolExecution,
    execution_status: str,
    result_summary: str | None = None,
    error_code: str | None = None,
) -> None:
    """
    Update the final state of a tool execution.
    """

    allowed_statuses = {
        "succeeded",
        "failed",
        "denied",
    }

    if execution_status not in allowed_statuses:
        raise ValueError(
            "Invalid final tool execution status."
        )

    execution.execution_status = execution_status
    execution.result_summary = result_summary
    execution.error_code = error_code
    execution.completed_at = datetime.now(timezone.utc)

    db.flush()


# ============================================================
# TOOL RESULT SUMMARIZATION
# ============================================================

def summarize_tool_result(
    result: Any,
    max_length: int = 500,
) -> str:
    """
    Generate a short audit summary without storing
    the complete potentially sensitive HR result.
    """

    if isinstance(result, dict):
        summary = (
            f"Operation completed. "
            f"Returned {len(result)} top-level fields."
        )

    elif isinstance(result, list):
        summary = (
            f"Operation completed. "
            f"Returned {len(result)} records."
        )

    elif result is None:
        summary = "Operation completed without a result."

    else:
        summary = "Operation completed successfully."

    return summary[:max_length]


# ============================================================
# SAFE TOOL HANDLER EXECUTION
# ============================================================

def invoke_tool_handler(
    db: Session,
    current_user: User,
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    """
    Execute a registered handler using trusted backend
    dependencies.

    Gemini arguments are never allowed to override db
    or current_user.
    """

    handler = tool_registry.get_handler(tool_name)

    return handler(
        db=db,
        current_user=current_user,
        **arguments,
    )


# ============================================================
# EXECUTE OR STAGE A TOOL CALL
# ============================================================

def execute_tool_call(
    db: Session,
    conversation_id: int,
    current_user: User,
    tool_name: str,
    arguments: dict[str, Any],
    message_id: int | None = None,
) -> dict[str, Any]:
    """
    Validate and authorize a Gemini tool call.

    Read operations:
        Execute immediately and record the result.

    Write operations:
        Create an awaiting_confirmation record.
        Never execute the write handler at this stage.
    """

    try:
        # ----------------------------------------------------
        # 1. VERIFY TOOL REGISTRATION
        # ----------------------------------------------------

        definition = tool_registry.get_definition(tool_name)

        if not tool_registry.is_executable(tool_name):
            raise ToolExecutionError(
                f"Tool '{tool_name}' has no registered handler."
            )

        # ----------------------------------------------------
        # 2. VALIDATE TOOL ARGUMENTS
        # ----------------------------------------------------

        validated_arguments = validate_tool_arguments(
            tool_name=tool_name,
            arguments=arguments,
        )

        # ----------------------------------------------------
        # 3. VERIFY CONVERSATION OWNERSHIP
        # ----------------------------------------------------

        verify_conversation_access(
            db=db,
            conversation_id=conversation_id,
            current_user=current_user,
        )

        # ----------------------------------------------------
        # 4. VERIFY USER PERMISSION
        # ----------------------------------------------------

        verify_tool_permission(
            db=db,
            current_user=current_user,
            tool_name=tool_name,
        )

        # ----------------------------------------------------
        # 5. CHECK TOOL OPERATION CONFIGURATION
        # ----------------------------------------------------

        if definition.operation_type == "write":

            if not definition.requires_confirmation:
                raise ToolExecutionError(
                    "Write tools must require explicit confirmation."
                )

        elif definition.requires_confirmation:
            raise ToolExecutionError(
                "Read tools cannot be configured as confirmation-required."
            )

        # ----------------------------------------------------
        # 6. STAGE WRITE OPERATIONS
        # ----------------------------------------------------

        if definition.operation_type == "write":

            execution = create_tool_execution_record(
                db=db,
                conversation_id=conversation_id,
                current_user=current_user,
                tool_name=tool_name,
                arguments=validated_arguments,
                message_id=message_id,
                execution_status="awaiting_confirmation",
            )

            execution_id = execution.tool_execution_id

            db.commit()

            logger.info(
                "AI write tool staged for confirmation. "
                "Tool: %s, Execution ID: %s, User ID: %s",
                tool_name,
                execution_id,
                current_user.user_id,
            )

            return {
                "success": True,
                "requires_confirmation": True,
                "execution_id": execution_id,
                "tool_name": tool_name,
                "message": (
                    "This operation requires your confirmation "
                    "before it can be executed."
                ),
            }

        # ----------------------------------------------------
        # 7. CREATE READ EXECUTION AUDIT RECORD
        # ----------------------------------------------------

        execution = create_tool_execution_record(
            db=db,
            conversation_id=conversation_id,
            current_user=current_user,
            tool_name=tool_name,
            arguments=validated_arguments,
            message_id=message_id,
            execution_status="started",
        )

        execution_id = execution.tool_execution_id

        # Persist the started state before calling the handler.
        db.commit()

        # ----------------------------------------------------
        # 8. EXECUTE READ HANDLER
        # ----------------------------------------------------

        result = invoke_tool_handler(
            db=db,
            current_user=current_user,
            tool_name=tool_name,
            arguments=validated_arguments,
        )

        # ----------------------------------------------------
        # 9. RECORD SUCCESS
        # ----------------------------------------------------

        complete_tool_execution(
            db=db,
            execution=execution,
            execution_status="succeeded",
            result_summary=summarize_tool_result(result),
        )

        db.commit()

        return {
            "success": True,
            "requires_confirmation": False,
            "execution_id": execution_id,
            "tool_name": tool_name,
            "result": result,
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "AI tool execution failed. Tool: %s, Error type: %s",
            tool_name,
            type(exc).__name__,
        )

        # Record failure only if an execution record
        # was successfully created and committed.
        if "execution_id" in locals():

            failed_execution = (
                db.query(AIToolExecution)
                .filter(
                    AIToolExecution.tool_execution_id == execution_id
                )
                .first()
            )

            if (
                failed_execution is not None
                and failed_execution.execution_status == "started"
            ):
                complete_tool_execution(
                    db=db,
                    execution=failed_execution,
                    execution_status="failed",
                    error_code=type(exc).__name__,
                )

                db.commit()

        return {
            "success": False,
            "requires_confirmation": False,
            "execution_id": locals().get("execution_id"),
            "tool_name": tool_name,
            "error": str(exc) if isinstance(
                exc,
                ToolExecutionError,
            ) else "The requested HRMS operation could not be completed.",
        }

# ============================================================
# CONFIRM PENDING WRITE OPERATION
# ============================================================

def confirm_tool_execution(
    db: Session,
    execution_id: int,
    conversation_id: int,
    current_user: User,
) -> dict[str, Any]:
    """
    Execute a pending write operation after explicit
    confirmation from the authenticated user.

    A database row lock prevents concurrent confirmation.
    Permissions and conversation ownership are checked again.
    """

    try:
        # ----------------------------------------------------
        # 1. LOCK THE PENDING EXECUTION RECORD
        # ----------------------------------------------------

        execution = (
            db.query(AIToolExecution)
            .filter(
                AIToolExecution.tool_execution_id == execution_id,
                AIToolExecution.conversation_id == conversation_id,
                AIToolExecution.user_id == current_user.user_id,
            )
            .with_for_update()
            .first()
        )

        if execution is None:
            raise ToolExecutionNotFoundError(
                "Pending tool execution was not found."
            )

        # ----------------------------------------------------
        # 2. VERIFY CONVERSATION OWNERSHIP
        # ----------------------------------------------------

        verify_conversation_access(
            db=db,
            conversation_id=conversation_id,
            current_user=current_user,
        )

        # ----------------------------------------------------
        # 3. VERIFY EXECUTION STATUS
        # ----------------------------------------------------

        if execution.execution_status != "awaiting_confirmation":
            raise ToolConfirmationError(
                "This operation is no longer awaiting confirmation."
            )

        # ----------------------------------------------------
        # 4. VERIFY TOOL CONFIGURATION
        # ----------------------------------------------------

        definition = tool_registry.get_definition(
            execution.tool_name
        )

        if (
            definition.operation_type != "write"
            or not definition.requires_confirmation
            or not tool_registry.is_executable(execution.tool_name)
        ):
            raise ToolConfirmationError(
                "This tool is not configured for confirmed execution."
            )

        # ----------------------------------------------------
        # 5. REVALIDATE ARGUMENTS AND PERMISSIONS
        # ----------------------------------------------------

        validated_arguments = validate_tool_arguments(
            tool_name=execution.tool_name,
            arguments=execution.input_arguments,
        )

        verify_tool_permission(
            db=db,
            current_user=current_user,
            tool_name=execution.tool_name,
        )

        # ----------------------------------------------------
        # 6. MARK AS STARTED BEFORE EXECUTION
        # ----------------------------------------------------

        execution.execution_status = "started"
        execution.started_at = datetime.now(timezone.utc)

        db.commit()

        # ----------------------------------------------------
        # 7. EXECUTE THE CONFIRMED WRITE HANDLER
        # ----------------------------------------------------

        result = invoke_tool_handler(
            db=db,
            current_user=current_user,
            tool_name=execution.tool_name,
            arguments=validated_arguments,
        )

        # ----------------------------------------------------
        # 8. RECORD SUCCESS
        # ----------------------------------------------------

        execution = (
            db.query(AIToolExecution)
            .filter(
                AIToolExecution.tool_execution_id == execution_id
            )
            .first()
        )

        complete_tool_execution(
            db=db,
            execution=execution,
            execution_status="succeeded",
            result_summary=summarize_tool_result(result),
        )

        db.commit()

        logger.info(
            "Confirmed AI write operation completed. "
            "Tool: %s, Execution ID: %s, User ID: %s",
            execution.tool_name,
            execution_id,
            current_user.user_id,
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "tool_name": execution.tool_name,
            "result": result,
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Confirmed AI tool execution failed. "
            "Execution ID: %s, Error type: %s",
            execution_id,
            type(exc).__name__,
        )

        # The started state was committed before the handler ran.
        # Record failure without reopening the confirmation.
        failed_execution = (
            db.query(AIToolExecution)
            .filter(
                AIToolExecution.tool_execution_id == execution_id,
                AIToolExecution.conversation_id == conversation_id,
                AIToolExecution.user_id == current_user.user_id,
                AIToolExecution.execution_status == "started",
            )
            .first()
        )

        if failed_execution is not None:
            complete_tool_execution(
                db=db,
                execution=failed_execution,
                execution_status="failed",
                error_code=type(exc).__name__,
            )
            db.commit()

        return {
            "success": False,
            "execution_id": execution_id,
            "error": str(exc) if isinstance(
                exc,
                ToolExecutionError,
            ) else "The confirmed HRMS operation could not be completed.",
        }


# ============================================================
# REJECT PENDING WRITE OPERATION
# ============================================================

def reject_tool_execution(
    db: Session,
    execution_id: int,
    conversation_id: int,
    current_user: User,
) -> dict[str, Any]:
    """
    Reject a pending write operation.

    The business handler is never executed.
    """

    try:
        # ----------------------------------------------------
        # 1. LOCK THE EXECUTION RECORD
        # ----------------------------------------------------

        execution = (
            db.query(AIToolExecution)
            .filter(
                AIToolExecution.tool_execution_id == execution_id,
                AIToolExecution.conversation_id == conversation_id,
                AIToolExecution.user_id == current_user.user_id,
            )
            .with_for_update()
            .first()
        )

        if execution is None:
            raise ToolExecutionNotFoundError(
                "Pending tool execution was not found."
            )

        # ----------------------------------------------------
        # 2. VERIFY CONVERSATION OWNERSHIP
        # ----------------------------------------------------

        verify_conversation_access(
            db=db,
            conversation_id=conversation_id,
            current_user=current_user,
        )

        # ----------------------------------------------------
        # 3. VERIFY PENDING STATUS
        # ----------------------------------------------------

        if execution.execution_status != "awaiting_confirmation":
            raise ToolConfirmationError(
                "This operation is no longer awaiting confirmation."
            )

        # ----------------------------------------------------
        # 4. MARK AS DENIED
        # ----------------------------------------------------

        execution.execution_status = "denied"
        execution.completed_at = datetime.now(timezone.utc)
        execution.result_summary = (
            "The user declined the requested operation."
        )

        db.commit()

        logger.info(
            "AI write operation rejected. "
            "Execution ID: %s, User ID: %s",
            execution_id,
            current_user.user_id,
        )

        return {
            "success": True,
            "execution_id": execution_id,
            "tool_name": execution.tool_name,
            "execution_status": "denied",
            "message": "The requested operation was not executed.",
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "AI tool rejection failed. "
            "Execution ID: %s, Error type: %s",
            execution_id,
            type(exc).__name__,
        )

        return {
            "success": False,
            "execution_id": execution_id,
            "error": str(exc) if isinstance(
                exc,
                ToolExecutionError,
            ) else "Unable to reject the requested operation.",
        }
