
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.ai_tools.executor import (
    confirm_tool_execution,
    reject_tool_execution,
)
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories import ai_assistant_repository as repository
from app.schemas.ai_assistant import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationStatus,
)
from app.services.ai_assistant_service import (
    AIAssistantService,
    AIAssistantServiceError,
    AIAssistantConversationError,
    AIAssistantGenerationError,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"],
)


# ------------------------------------------------------------
# CREATE CONVERSATION
# ------------------------------------------------------------

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    request: ConversationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conversation = repository.create_conversation(
        db=db,
        user_id=current_user.user_id,
        title=request.title,
    )

    db.commit()
    db.refresh(conversation)

    return conversation


# ------------------------------------------------------------
# LIST USER CONVERSATIONS
# ------------------------------------------------------------

@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    conversation_status: Annotated[
        ConversationStatus | None,
        Query(alias="status"),
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return repository.get_user_conversations(
        db=db,
        user_id=current_user.user_id,
        conversation_status=conversation_status,
        skip=skip,
        limit=limit,
    )


# ------------------------------------------------------------
# GET CONVERSATION WITH MESSAGE HISTORY
# ------------------------------------------------------------

@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conversation = repository.get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.user_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = repository.get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
    )

    return {
        "conversation_id": conversation.conversation_id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "status": conversation.status,
        "started_at": conversation.started_at,
        "last_message_at": conversation.last_message_at,
        "ended_at": conversation.ended_at,
        "messages": messages,
    }


# ------------------------------------------------------------
# CLOSE CONVERSATION
# ------------------------------------------------------------

@router.post(
    "/conversations/{conversation_id}/close",
    response_model=ConversationResponse,
)
def close_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conversation = repository.get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.user_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active conversations can be closed.",
        )

    repository.update_conversation_status(
        conversation=conversation,
        new_status="closed",
    )

    db.commit()
    db.refresh(conversation)

    return conversation


# ------------------------------------------------------------
# ARCHIVE CONVERSATION
# ------------------------------------------------------------

@router.post(
    "/conversations/{conversation_id}/archive",
    response_model=ConversationResponse,
)
def archive_conversation(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    conversation = repository.get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.user_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if conversation.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conversation is already archived.",
        )

    repository.update_conversation_status(
        conversation=conversation,
        new_status="archived",
    )

    db.commit()
    db.refresh(conversation)

    return conversation


# ------------------------------------------------------------
# AI CHAT
# ------------------------------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat_with_assistant(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Send a message to the AI HRMS Assistant.

    Creates a conversation when conversation_id is not supplied.
    Existing conversations are accessible only to their owners.
    """

    service = AIAssistantService()

    try:
        return service.chat(
            db=db,
            current_user=current_user,
            message=request.message,
            conversation_id=request.conversation_id,
        )

    except AIAssistantConversationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AIAssistantGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI Assistant could not generate a response.",
        ) from exc

    except AIAssistantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI Assistant could not process your request.",
        ) from exc


# ------------------------------------------------------------
# CONFIRM PENDING TOOL EXECUTION
# ------------------------------------------------------------

@router.post(
    "/conversations/{conversation_id}/tool-executions/{execution_id}/confirm",
    status_code=status.HTTP_200_OK,
)
def confirm_ai_tool_execution(
    conversation_id: int,
    execution_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return confirm_tool_execution(
        db=db,
        execution_id=execution_id,
        conversation_id=conversation_id,
        current_user=current_user,
    )


# ------------------------------------------------------------
# REJECT PENDING TOOL EXECUTION
# ------------------------------------------------------------

@router.post(
    "/conversations/{conversation_id}/tool-executions/{execution_id}/reject",
    status_code=status.HTTP_200_OK,
)
def reject_ai_tool_execution(
    conversation_id: int,
    execution_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return reject_tool_execution(
        db=db,
        execution_id=execution_id,
        conversation_id=conversation_id,
        current_user=current_user,
    )