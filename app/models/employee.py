
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    employee_code = Column(
        String(20),
        unique=True,
        nullable=False,
        server_default=text(
            "('EMP'::text || "
            "lpad((nextval('employee_code_seq'::regclass))::text, 3, '0'))"
        ),
    )

    full_name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Retain the existing legacy department column.
    department = Column(
        String(100),
        nullable=True,
    )

    job_title = Column(
        String(100),
        nullable=True,
    )

    hire_date = Column(
        Date,
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

    department_id = Column(
        BigInteger,
        ForeignKey(
            "departments.department_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    manager_employee_id = Column(
        BigInteger,
        ForeignKey(
            "employees.employee_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    department_info = relationship(
        "Department",
        back_populates="employees",
    )

    manager = relationship(
        "Employee",
        remote_side=[employee_id],
        back_populates="direct_reports",
    )

    direct_reports = relationship(
        "Employee",
        back_populates="manager",
    )
    user = relationship(
        "User",
        back_populates="employee",
        uselist=False,
    )
    @property
    def department_display(self) -> str | None:
        """
        Return the department name from the relationship.

        Fall back to the legacy department column
        for backward compatibility.
        """

        if self.department_info is not None:
            return self.department_info.department_name

        return self.department