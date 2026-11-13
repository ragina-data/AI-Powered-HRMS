from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class AIConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    user_id: int
    title: str | None
    status: str
    started_at: datetime
    last_message_at: datetime | None
    ended_at: datetime | None


class AIMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class AIMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    conversation_id: int
    sender_type: Literal["user", "assistant", "system"]
    content: str
    model_name: str | None
    token_count: int | None
    created_at: datetime



"""
AI Assistant Schemas
====================

Purpose:
    Define request and response schemas for the AI Virtual Assistant.

Responsibilities:
    1. Validate conversation creation requests.
    2. Validate employee chat messages.
    3. Define conversation response structures.
    4. Define message response structures.
    5. Define complete chat response structures.

Security:
    Sender identity and conversation ownership are determined
    by the authenticated backend user, never by request input.
"""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# STATUS AND SENDER TYPES
# ============================================================

ConversationStatus = Literal[
    "active",
    "closed",
    "archived",
]

MessageSenderType = Literal[
    "user",
    "assistant",
    "system",
    "tool",
]


# ============================================================
# 1. CONVERSATION CREATION
# ============================================================

class ConversationCreate(BaseModel):
    """
    Request schema for creating a new conversation.
    """

    title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional conversation title.",
    )


# ============================================================
# 2. CONVERSATION RESPONSE
# ============================================================

class ConversationResponse(BaseModel):
    """
    Response schema for conversation information.
    """

    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    user_id: int
    title: str | None
    status: ConversationStatus
    started_at: datetime
    last_message_at: datetime | None
    ended_at: datetime | None


# ============================================================
# 3. CHAT REQUEST
# ============================================================

class ChatRequest(BaseModel):
    """
    Request schema for sending a message to the AI Assistant.

    conversation_id:
        Existing conversation ID.
        None means create a new conversation.

    message:
        Employee's natural language question.
    """

    conversation_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Existing conversation ID. "
            "Leave null to start a new conversation."
        ),
    )

    message: str = Field(
        min_length=1,
        max_length=10000,
        description="Employee's question or message.",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Message cannot contain only whitespace."
            )

        return value


# ============================================================
# 4. MESSAGE RESPONSE
# ============================================================

class MessageResponse(BaseModel):
    """
    Response schema for an individual conversation message.
    """

    model_config = ConfigDict(from_attributes=True)

    message_id: int
    conversation_id: int

    sender_type: MessageSenderType

    content: str

    model_name: str | None
    token_count: int | None

    created_at: datetime


# ============================================================
# 5. CHAT RESPONSE
# ============================================================

class ChatResponse(BaseModel):
    """
    Response returned after processing an employee message.

    Contains both the employee message and AI response.
    """

    conversation_id: int

    user_message: MessageResponse

    assistant_message: MessageResponse


# ============================================================
# 6. CONVERSATION DETAIL RESPONSE
# ============================================================

class ConversationDetailResponse(ConversationResponse):
    """
    Conversation details including the complete message history.
    """

    messages: list[MessageResponse] = Field(
        default_factory=list
    )
