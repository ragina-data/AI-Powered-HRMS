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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_log_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    actor_user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    action = Column(
        String(100),
        nullable=False,
    )

    entity_type = Column(
        String(100),
        nullable=True,
    )

    entity_id = Column(
        String(100),
        nullable=True,
    )

    details = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    actor = relationship("User")