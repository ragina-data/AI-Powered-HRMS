
from app.ai_tools import executor
from app.models.ai_conversation import AIConversation
from app.models.ai_tool_execution import AIToolExecution


def create_pending_execution(db_session, user):
    conversation = AIConversation(
        user_id=user.user_id,
        status="active",
    )
    db_session.add(conversation)
    db_session.flush()

    execution = AIToolExecution(
        conversation_id=conversation.conversation_id,
        user_id=user.user_id,
        tool_name="submit_leave_request",
        input_arguments={
            "leave_type": "annual",
            "start_date": "2026-12-01",
            "end_date": "2026-12-02",
            "reason": "Personal leave",
            "medical_certificate_submitted": False,
        },
        execution_status="awaiting_confirmation",
    )
    db_session.add(execution)
    db_session.flush()

    return conversation, execution


def allow_permission(monkeypatch):
    monkeypatch.setattr(
        executor,
        "user_has_permission",
        lambda **kwargs: True,
    )


def test_write_tool_waits_for_confirmation(
    db_session,
    document_test_accounts,
    monkeypatch,
):
    user = document_test_accounts.employee_user
    conversation = AIConversation(
        user_id=user.user_id,
        status="active",
    )
    db_session.add(conversation)
    db_session.flush()

    allow_permission(monkeypatch)

    handler_calls = []

    monkeypatch.setattr(
        executor.tool_registry,
        "get_handler",
        lambda name: lambda **kwargs: handler_calls.append(kwargs),
    )

    result = executor.execute_tool_call(
        db=db_session,
        conversation_id=conversation.conversation_id,
        current_user=user,
        tool_name="submit_leave_request",
        arguments={
            "leave_type": "annual",
            "start_date": "2026-12-01",
            "end_date": "2026-12-02",
            "reason": "Personal leave",
            "medical_certificate_submitted": False,
        },
    )

    assert result["success"] is True
    assert result["requires_confirmation"] is True
    assert result["execution_id"] is not None
    assert handler_calls == []

    execution = (
        db_session.query(AIToolExecution)
        .filter(
            AIToolExecution.tool_execution_id
            == result["execution_id"]
        )
        .one()
    )

    assert execution.execution_status == "awaiting_confirmation"


def test_confirm_executes_write_handler(
    db_session,
    document_test_accounts,
    monkeypatch,
):
    user = document_test_accounts.employee_user
    conversation, execution = create_pending_execution(
        db_session,
        user,
    )

    allow_permission(monkeypatch)

    handler_calls = []

    monkeypatch.setattr(
        executor.tool_registry,
        "get_handler",
        lambda name: lambda **kwargs: (
            handler_calls.append(kwargs)
            or {"leave_request_id": 123}
        ),
    )

    result = executor.confirm_tool_execution(
        db=db_session,
        execution_id=execution.tool_execution_id,
        conversation_id=conversation.conversation_id,
        current_user=user,
    )

    assert result["success"] is True
    assert result["tool_name"] == "submit_leave_request"
    assert result["result"] == {"leave_request_id": 123}
    assert len(handler_calls) == 1

    db_session.refresh(execution)
    assert execution.execution_status == "succeeded"
    assert execution.completed_at is not None


def test_reject_does_not_execute_handler(
    db_session,
    document_test_accounts,
    monkeypatch,
):
    user = document_test_accounts.employee_user
    conversation, execution = create_pending_execution(
        db_session,
        user,
    )

    handler_calls = []

    monkeypatch.setattr(
        executor.tool_registry,
        "get_handler",
        lambda name: lambda **kwargs: handler_calls.append(kwargs),
    )

    result = executor.reject_tool_execution(
        db=db_session,
        execution_id=execution.tool_execution_id,
        conversation_id=conversation.conversation_id,
        current_user=user,
    )

    assert result["success"] is True
    assert result["execution_status"] == "denied"
    assert handler_calls == []

    db_session.refresh(execution)
    assert execution.execution_status == "denied"
    assert execution.completed_at is not None


def test_repeated_confirmation_is_prevented(
    db_session,
    document_test_accounts,
    monkeypatch,
):
    user = document_test_accounts.employee_user
    conversation, execution = create_pending_execution(
        db_session,
        user,
    )

    allow_permission(monkeypatch)

    handler_calls = []

    monkeypatch.setattr(
        executor.tool_registry,
        "get_handler",
        lambda name: lambda **kwargs: (
            handler_calls.append(kwargs) or {"success": True}
        ),
    )

    first_result = executor.confirm_tool_execution(
        db=db_session,
        execution_id=execution.tool_execution_id,
        conversation_id=conversation.conversation_id,
        current_user=user,
    )

    second_result = executor.confirm_tool_execution(
        db=db_session,
        execution_id=execution.tool_execution_id,
        conversation_id=conversation.conversation_id,
        current_user=user,
    )

    assert first_result["success"] is True
    assert second_result["success"] is False
    assert len(handler_calls) == 1


def test_confirmation_fails_when_permission_is_revoked(
    db_session,
    document_test_accounts,
    monkeypatch,
):
    user = document_test_accounts.employee_user
    conversation, execution = create_pending_execution(
        db_session,
        user,
    )
    db_session.commit()

    monkeypatch.setattr(
        executor,
        "user_has_permission",
        lambda **kwargs: False,
    )

    handler_calls = []

    monkeypatch.setattr(
        executor.tool_registry,
        "get_handler",
        lambda name: lambda **kwargs: handler_calls.append(kwargs),
    )

    result = executor.confirm_tool_execution(
        db=db_session,
        execution_id=execution.tool_execution_id,
        conversation_id=conversation.conversation_id,
        current_user=user,
    )

    assert result["success"] is False
    assert handler_calls == []


    assert result["success"] is False
    assert handler_calls == []

    pending_execution = (
        db_session.query(AIToolExecution)
        .filter(
            AIToolExecution.tool_execution_id
            == execution.tool_execution_id
        )
        .one()
    )
    assert pending_execution.execution_status == "awaiting_confirmation"