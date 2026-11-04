
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    role_name = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete",
    )

    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete",
    )
