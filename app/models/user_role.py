
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id = Column(
        BigInteger,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    role = relationship(
        "Role",
        back_populates="user_roles",
    )

    user = relationship(
        "User",
        back_populates="user_roles",
    )
