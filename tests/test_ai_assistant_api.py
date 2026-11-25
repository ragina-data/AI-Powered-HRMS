
from datetime import datetime, timezone


def test_ai_chat_rejects_unauthenticated_request(integration_client):
    response = integration_client.post(
        "/api/v1/ai/chat",
        json={
            "message": "What is my leave balance?"
        },
    )

    assert response.status_code == 401


def test_ai_chat_requires_valid_chat_response(
    integration_client,
    document_test_accounts,
    monkeypatch,
):
    from app.api.deps import get_current_user
    from app.api.ai_assistant import AIAssistantService
    from app.main import app

    user = document_test_accounts.employee_user

    app.dependency_overrides[get_current_user] = lambda: user

    def mock_chat(
        self,
        db,
        current_user,
        message,
        conversation_id=None,
    ):
        now = datetime.now(timezone.utc)

        return {
            "conversation_id": 1,
            "user_message": {
                "message_id": 1,
                "conversation_id": 1,
                "sender_type": "user",
                "content": message,
                "model_name": None,
                "token_count": None,
                "created_at": now,
            },
            "assistant_message": {
                "message_id": 2,
                "conversation_id": 1,
                "sender_type": "assistant",
                "content": "Your leave balance is 15 days.",
                "model_name": "mock-gemini",
                "token_count": 10,
                "created_at": now,
            },
        }

    monkeypatch.setattr(
        AIAssistantService,
        "chat",
        mock_chat,
    )

    try:
        response = integration_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "What is my leave balance?"
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200

    data = response.json()

    assert data["conversation_id"] == 1
    assert data["user_message"]["content"] == (
        "What is my leave balance?"
    )
    assert data["assistant_message"]["content"] == (
        "Your leave balance is 15 days."
    )


def test_ai_tool_execution_confirmation_api(
    integration_client,
    document_test_accounts,
    monkeypatch,
):
    from app.api.deps import get_current_user
    from app.main import app
    from app.api import ai_assistant

    app.dependency_overrides[get_current_user] = (
        lambda: document_test_accounts.employee_user
    )

    monkeypatch.setattr(
        ai_assistant,
        "confirm_tool_execution",
        lambda **kwargs: {
            "success": True,
            "execution_id": kwargs["execution_id"],
            "tool_name": "request_leave",
            "result": {
                "message": "Leave request submitted."
            },
        },
    )

    try:
        response = integration_client.post(
            "/api/v1/ai/conversations/1/tool-executions/10/confirm"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["execution_id"] == 10
    assert data["tool_name"] == "request_leave"


def test_ai_tool_execution_rejection_api(
    integration_client,
    document_test_accounts,
    monkeypatch,
):
    from app.api.deps import get_current_user
    from app.main import app
    from app.api import ai_assistant

    app.dependency_overrides[get_current_user] = (
        lambda: document_test_accounts.employee_user
    )

    monkeypatch.setattr(
        ai_assistant,
        "reject_tool_execution",
        lambda **kwargs: {
            "success": True,
            "execution_id": kwargs["execution_id"],
            "tool_name": "request_leave",
            "execution_status": "denied",
            "message": "The requested operation was not executed.",
        },
    )

    try:
        response = integration_client.post(
            "/api/v1/ai/conversations/1/tool-executions/10/reject"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["execution_id"] == 10
    assert data["execution_status"] == "denied"
