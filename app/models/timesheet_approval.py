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


class TimesheetApproval(Base):
    __tablename__ = "timesheet_approvals"

    timesheet_approval_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    timesheet_id = Column(
        BigInteger,
        ForeignKey(
            "timesheets.timesheet_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    approver_employee_id = Column(
        BigInteger,
        ForeignKey(
            "employees.employee_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    decision = Column(
        String(20),
        nullable=False,
    )

    comments = Column(
        Text,
        nullable=True,
    )

    decided_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    timesheet = relationship(
        "Timesheet",
        back_populates="approvals",
    )

    approver_employee = relationship("Employee")