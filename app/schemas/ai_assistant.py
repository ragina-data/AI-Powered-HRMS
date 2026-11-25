
"""
AI Assistant Schemas
====================

Purpose:
    Define request and response schemas for the AI Virtual Assistant.

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


class ConversationCreate(BaseModel):
    """Request schema for creating a new conversation."""

    title: str | None = Field(
        default=None,
        max_length=200,
    )


class ConversationResponse(BaseModel):
    """Response schema for conversation information."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    user_id: int
    title: str | None
    status: ConversationStatus
    started_at: datetime
    last_message_at: datetime | None
    ended_at: datetime | None


class ChatRequest(BaseModel):
    """Request schema for sending a message to the AI Assistant."""

    conversation_id: int | None = Field(
        default=None,
        gt=0,
    )

    message: str = Field(
        min_length=1,
        max_length=10000,
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


class MessageResponse(BaseModel):
    """Response schema for an individual conversation message."""

    model_config = ConfigDict(from_attributes=True)

    message_id: int
    conversation_id: int
    sender_type: MessageSenderType
    content: str
    model_name: str | None
    token_count: int | None
    created_at: datetime

class PendingConfirmationResponse(BaseModel):
    """A write operation waiting for employee confirmation."""

    execution_id: int
    tool_name: str

class ChatResponse(BaseModel):
    """Response returned after processing an employee message."""

    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse
    pending_confirmations: list[PendingConfirmationResponse] = Field(
        default_factory=list
    )


class ConversationDetailResponse(ConversationResponse):
    """Conversation details including complete message history."""

    messages: list[MessageResponse] = Field(
        default_factory=list
    )
