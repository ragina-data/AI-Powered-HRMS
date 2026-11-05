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