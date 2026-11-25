
from unittest.mock import MagicMock

from app.services.ai_assistant_service import (
    AIAssistantService,
    AIAssistantConversationError,
)


def test_service_can_be_created():
    service = AIAssistantService(gemini_client=MagicMock())

    assert service is not None


def test_authorized_tools_are_filtered_by_permission(monkeypatch):
    from app.services import ai_assistant_service

    service = AIAssistantService(gemini_client=MagicMock())

    db = MagicMock()
    current_user = MagicMock()

    monkeypatch.setattr(
        ai_assistant_service.tool_registry,
        "list_executable_tools",
        lambda: [
            ai_assistant_service.tool_registry.get_definition(
                "get_my_employee_profile"
            )
        ],
    )

    monkeypatch.setattr(
        ai_assistant_service,
        "get_authorized_tools",
        lambda *args, **kwargs: [],
        raising=False,
    )

    monkeypatch.setattr(
        ai_assistant_service,
        "user_has_permission",
        lambda db, user_id, permission_code: False,
    )

    result = service._get_authorized_tool_definitions(
        db,
        current_user,
    )

    assert result == []

def test_authorized_tools_include_permitted_tool(monkeypatch):
    from app.services import ai_assistant_service

    service = AIAssistantService(gemini_client=MagicMock())

    db = MagicMock()
    current_user = MagicMock()
    current_user.user_id = 1

    definition = ai_assistant_service.tool_registry.get_definition(
        "get_my_employee_profile"
    )

    monkeypatch.setattr(
        ai_assistant_service.tool_registry,
        "list_executable_tools",
        lambda: [definition],
    )

    monkeypatch.setattr(
        ai_assistant_service,
        "user_has_permission",
        lambda db, user_id, permission_code: True,
    )

    result = service._get_authorized_tool_definitions(
        db,
        current_user,
    )

    assert len(result) == 1
    assert result[0].name == "get_my_employee_profile"
