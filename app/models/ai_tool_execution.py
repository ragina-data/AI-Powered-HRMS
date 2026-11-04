from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class AIToolExecution(Base):
    __tablename__ = "ai_tool_executions"

    tool_execution_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    conversation_id = Column(
        BigInteger,
        ForeignKey(
            "ai_conversations.conversation_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    message_id = Column(
        BigInteger,
        ForeignKey(
            "ai_messages.message_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    tool_name = Column(
        String(100),
        nullable=False,
    )

    input_arguments = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    execution_status = Column(
        String(20),
        nullable=False,
        server_default=text("'started'"),
    )

    result_summary = Column(
        Text,
        nullable=True,
    )

    error_code = Column(
        String(100),
        nullable=True,
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    conversation = relationship("AIConversation")
    message = relationship("AIMessage")
    user = relationship("User")