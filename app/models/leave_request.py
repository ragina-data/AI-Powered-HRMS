from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    leave_request_id = Column(
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

    start_date = Column(Date, nullable=False)

    end_date = Column(Date, nullable=False)

    days_requested = Column(Numeric, nullable=False)

    reason = Column(Text, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
    )

    submitted_at = Column(
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
        back_populates="leave_requests",
        foreign_keys=[leave_type],
    )

    transactions = relationship(
        "LeaveTransaction",
        back_populates="leave_request",
    )