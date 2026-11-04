from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    leave_balance_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    employee_id = Column(
        BigInteger,
        ForeignKey(
            "employees.employee_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    leave_type = Column(
        String(30),
        ForeignKey(
            "leave_types.leave_type_code",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    entitlement_days = Column(
        Numeric,
        nullable=False,
        server_default=text("0"),
    )

    used_days = Column(
        Numeric,
        nullable=False,
        server_default=text("0"),
    )

    balance_year = Column(
        Integer,
        nullable=False,
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

    employee = relationship("Employee")

    leave_type_info = relationship(
        "LeaveType",
        back_populates="leave_balances",
        foreign_keys=[leave_type],
    )

    transactions = relationship(
        "LeaveTransaction",
        back_populates="leave_balance",
    )