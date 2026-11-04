from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveTransaction(Base):
    __tablename__ = "leave_transactions"

    leave_transaction_id = Column(
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

    leave_balance_id = Column(
        BigInteger,
        ForeignKey(
            "leave_balances.leave_balance_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    leave_request_id = Column(
        BigInteger,
        ForeignKey(
            "leave_requests.leave_request_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    transaction_type = Column(
        String(20),
        nullable=False,
    )

    days_delta = Column(
        Numeric,
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
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

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    leave_balance = relationship(
        "LeaveBalance",
        back_populates="transactions",
    )

    leave_request = relationship(
        "LeaveRequest",
        back_populates="transactions",
    )

    employee = relationship("Employee")

    actor_user = relationship("User")