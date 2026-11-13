
"""
AI Assistant Repository
=======================

Purpose:
    Handle PostgreSQL database operations for AI conversations
    and messages.

Responsibilities:
    1. Create conversations.
    2. Retrieve conversations owned by a user.
    3. List user conversations.
    4. Update conversation activity.
    5. Close and archive conversations.
    6. Create user, assistant and tool messages.
    7. Retrieve conversation messages.
    8. Retrieve recent messages for AI context.

Transaction management:
    No commits or rollbacks are performed here.
    The service layer controls transactions.

Security:
    Conversation retrieval is scoped by authenticated user_id.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage


# ============================================================
# 1. CREATE CONVERSATION
# ============================================================

def create_conversation(
    db: Session,
    user_id: int,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AIConversation:
    """
    Create a new conversation for an authenticated user.
    """

    conversation = AIConversation(
        user_id=user_id,
        title=title,
        status="active",
        conversation_metadata=metadata or {},
    )

    db.add(conversation)
    db.flush()

    return conversation


# ============================================================
# 2. RETRIEVE USER-OWNED CONVERSATION
# ============================================================

def get_conversation_by_id(
    db: Session,
    conversation_id: int,
    user_id: int,
    for_update: bool = False,
) -> AIConversation | None:
    """
    Retrieve a conversation only when it belongs to the user.

    Optional row locking supports safe concurrent operations.
    """

    query = db.query(AIConversation).filter(
        AIConversation.conversation_id == conversation_id,
        AIConversation.user_id == user_id,
    )

    if for_update:
        query = query.with_for_update()

    return query.first()


# ============================================================
# 3. LIST USER CONVERSATIONS
# ============================================================

def get_user_conversations(
    db: Session,
    user_id: int,
    conversation_status: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[AIConversation]:
    """
    Retrieve conversations belonging to one user.

    Most recently active conversations appear first.
    """

    query = db.query(AIConversation).filter(
        AIConversation.user_id == user_id
    )

    if conversation_status is not None:
        query = query.filter(
            AIConversation.status == conversation_status
        )

    return (
        query
        .order_by(
            AIConversation.last_message_at.desc().nullslast(),
            AIConversation.started_at.desc(),
            AIConversation.conversation_id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# 4. UPDATE CONVERSATION ACTIVITY
# ============================================================

def update_conversation_activity(
    conversation: AIConversation,
) -> None:
    """
    Update the last-message timestamp.

    This function does not commit the transaction.
    """

    conversation.last_message_at = datetime.now(timezone.utc)


# ============================================================
# 5. UPDATE CONVERSATION TITLE
# ============================================================

def update_conversation_title(
    conversation: AIConversation,
    title: str,
) -> None:
    """
    Update the conversation title.
    """

    conversation.title = title


# ============================================================
# 6. UPDATE CONVERSATION STATUS
# ============================================================

def update_conversation_status(
    conversation: AIConversation,
    new_status: str,
) -> None:
    """
    Update conversation status.

    Supported statuses:
        active
        closed
        archived

    The service layer must validate permitted transitions.
    """

    conversation.status = new_status

    if new_status == "closed":
        conversation.ended_at = datetime.now(timezone.utc)

    elif new_status == "active":
        conversation.ended_at = None


# ============================================================
# 7. CREATE MESSAGE
# ============================================================

def create_message(
    db: Session,
    conversation_id: int,
    sender_type: str,
    content: str,
    model_name: str | None = None,
    token_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> AIMessage:
    """
    Store a message belonging to a conversation.

    Supported sender types:
        user
        assistant
        system
        tool
    """

    message = AIMessage(
        conversation_id=conversation_id,
        sender_type=sender_type,
        content=content,
        model_name=model_name,
        token_count=token_count,
        message_metadata=metadata or {},
    )

    db.add(message)
    db.flush()

    return message


# ============================================================
# 8. RETRIEVE CONVERSATION MESSAGES
# ============================================================

def get_conversation_messages(
    db: Session,
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[AIMessage]:
    """
    Retrieve messages in chronological order.
    """

    return (
        db.query(AIMessage)
        .filter(
            AIMessage.conversation_id == conversation_id
        )
        .order_by(
            AIMessage.created_at.asc(),
            AIMessage.message_id.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# 9. RETRIEVE RECENT MESSAGES FOR AI CONTEXT
# ============================================================

def get_recent_messages(
    db: Session,
    conversation_id: int,
    limit: int = 10,
) -> list[AIMessage]:
    """
    Retrieve the most recent messages for conversational context.

    Results are returned in chronological order so they can
    be supplied to the language model in sequence.
    """

    messages = (
        db.query(AIMessage)
        .filter(
            AIMessage.conversation_id == conversation_id
        )
        .order_by(
            AIMessage.created_at.desc(),
            AIMessage.message_id.desc(),
        )
        .limit(limit)
        .all()
    )

    return list(reversed(messages))
