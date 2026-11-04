
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    department_name = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    department_code = Column(
        String(30),
        unique=True,
        nullable=True,
    )

    parent_department_id = Column(
        BigInteger,
        ForeignKey(
            "departments.department_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
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

    parent_department = relationship(
        "Department",
        remote_side=[department_id],
        back_populates="sub_departments",
    )

    sub_departments = relationship(
        "Department",
        back_populates="parent_department",
    )

    employees = relationship(
        "Employee",
        back_populates="department_info",
    )
