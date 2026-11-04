from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    text
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveApproval(Base):
    __tablename__ = "leave_approvals"

    leave_approval_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    leave_request_id = Column(
        BigInteger,
        ForeignKey(
            "leave_requests.leave_request_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION"
        ),
        nullable=False
    )

    approver_employee_id = Column(
        BigInteger,
        ForeignKey(
            "employees.employee_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION"
        ),
        nullable=False
    )

    decision = Column(String(20), nullable=False)

    comments = Column(Text, nullable=True)

    decided_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    leave_request = relationship("LeaveRequest")

    approver_employee = relationship(
        "Employee",
        foreign_keys=[approver_employee_id]
    )