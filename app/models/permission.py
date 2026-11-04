
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


class Permission(Base):
    __tablename__ = "permissions"

    permission_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    permission_code = Column(
        String(100),
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

    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete",
    )
