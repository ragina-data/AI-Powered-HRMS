from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class AIMessage(Base):
    __tablename__ = "ai_messages"

    message_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    conversation_id = Column(
        BigInteger,
        ForeignKey(
            "ai_conversations.conversation_id",
            ondelete="CASCADE",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    sender_type = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    model_name = Column(
        String(100),
        nullable=True,
    )

    token_count = Column(
        Integer,
        nullable=True,
    )

    # "metadata" is reserved by SQLAlchemy's declarative Base.
    message_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    conversation = relationship(
        "AIConversation",
        back_populates="messages",
    )