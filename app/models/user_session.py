from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    CheckConstraint,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

import uuid

class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    session_family_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    default=uuid.uuid4,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    refresh_token_hash = Column(
        String(64),
        nullable=False,
    )

    access_token_jti = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    replaced_by_session_id = Column(
        BigInteger,
        ForeignKey(
            "user_sessions.session_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # User relationship
    user = relationship(
        "User",
        back_populates="sessions",
    )

    # Self-referencing session replacement relationship
    replaced_by = relationship(
        "UserSession",
        remote_side=[session_id],
        foreign_keys=[replaced_by_session_id],
        back_populates="replaced_sessions",
        uselist=False,
    )

    replaced_sessions = relationship(
        "UserSession",
        foreign_keys=[replaced_by_session_id],
        back_populates="replaced_by",
    )

    __table_args__ = (
        UniqueConstraint(
            "refresh_token_hash",
            name="uq_user_sessions_refresh_token",
        ),
        UniqueConstraint(
            "access_token_jti",
            name="uq_user_sessions_access_jti",
        ),
        CheckConstraint(
            "refresh_token_hash ~ '^[0-9a-f]{64}$'",
            name="chk_user_sessions_refresh_hash",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="chk_user_sessions_expiration",
        ),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="chk_user_sessions_revocation",
        ),
        CheckConstraint(
            "replaced_by_session_id IS NULL "
            "OR replaced_by_session_id <> session_id",
            name="chk_user_sessions_replacement",
        ),
        Index(
            "idx_user_sessions_user_id",
            "user_id",
        ),
        Index(
            "idx_user_sessions_active",
            "user_id",
            "expires_at",
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index(
            "idx_user_sessions_family_id",
            "session_family_id",
        ),
    )