from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    leave_type_code = Column(
        String(30),
        unique=True,
        nullable=False,
    )

    leave_type_name = Column(
        String(100),
        nullable=False,
    )

    description = Column(Text, nullable=True)

    is_paid = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    requires_approval = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    min_notice_calendar_days = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    max_consecutive_days = Column(
        Numeric,
        nullable=True,
    )

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

    entitlement_rules = relationship(
        "LeaveEntitlementRule",
        back_populates="leave_type",
    )

    leave_balances = relationship(
        "LeaveBalance",
        back_populates="leave_type_info",
    )

    leave_requests = relationship(
        "LeaveRequest",
        back_populates="leave_type_info",
    )