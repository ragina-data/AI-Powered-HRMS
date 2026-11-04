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


class Timesheet(Base):
    __tablename__ = "timesheets"

    timesheet_id = Column(
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

    period_start = Column(Date, nullable=False)

    period_end = Column(Date, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'draft'"),
    )

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    total_hours = Column(
        Numeric(7, 2),
        nullable=False,
        server_default=text("0"),
    )

    employee_comments = Column(Text, nullable=True)

    reviewer_comments = Column(Text, nullable=True)

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

    entries = relationship(
        "TimesheetEntry",
        back_populates="timesheet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    approvals = relationship(
        "TimesheetApproval",
        back_populates="timesheet",
    )