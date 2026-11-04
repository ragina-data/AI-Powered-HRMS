from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    conversation_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    title = Column(
        String(200),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'active'"),
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    last_message_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Python attribute is conversation_metadata because
    # "metadata" is reserved by SQLAlchemy's declarative Base.
    conversation_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    user = relationship("User")

    messages = relationship(
    "AIMessage",
    back_populates="conversation",
    cascade="all, delete-orphan",
    passive_deletes=True,
)