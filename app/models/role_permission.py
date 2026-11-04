
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(
        BigInteger,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )

    permission_id = Column(
        BigInteger,
        ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        primary_key=True,
    )

    role = relationship(
        "Role",
        back_populates="role_permissions",
    )

    permission = relationship(
        "Permission",
        back_populates="role_permissions",
    )
