from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class HRPolicy(Base):
    __tablename__ = "hr_policies"

    policy_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    policy_code = Column(
        String(50),
        nullable=False,
    )

    policy_title = Column(
        String(250),
        nullable=False,
    )

    policy_category = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    department_id = Column(
        BigInteger,
        ForeignKey(
            "departments.department_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    owner_user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'draft'"),
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

    department = relationship("Department")
    owner = relationship("User")