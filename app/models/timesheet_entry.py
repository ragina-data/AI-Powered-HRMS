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


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"

    timesheet_entry_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    timesheet_id = Column(
        BigInteger,
        ForeignKey(
            "timesheets.timesheet_id",
            ondelete="CASCADE",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    work_date = Column(
        Date,
        nullable=False,
    )

    hours_worked = Column(
        Numeric(5, 2),
        nullable=False,
    )

    task_description = Column(
        Text,
        nullable=True,
    )

    project_code = Column(
        String(100),
        nullable=True,
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

    timesheet = relationship(
        "Timesheet",
        back_populates="entries",
    )