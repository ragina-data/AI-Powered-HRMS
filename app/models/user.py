from sqlalchemy.orm import relationship
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)

    employee_id = Column(
        BigInteger,
        ForeignKey("employees.employee_id", ondelete="NO ACTION"),
        unique=True,
        nullable=True,
    )

    email = Column(String(255), unique=True, nullable=False)

    password_hash = Column(Text, nullable=False)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete",
    )
