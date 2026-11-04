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


class HRDocumentRequest(Base):
    __tablename__ = "hr_document_requests"

    document_request_id = Column(
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

    document_type = Column(
        String(50),
        ForeignKey(
            "hr_document_types.document_type_code",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    purpose = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
    )

    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    processed_by_employee_id = Column(
        BigInteger,
        ForeignKey(
            "employees.employee_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    remarks = Column(
        Text,
        nullable=True,
    )

    document_reference = Column(
        String(255),
        nullable=True,
    )

    employee = relationship(
        "Employee",
        foreign_keys=[employee_id],
    )

    processed_by_employee = relationship(
        "Employee",
        foreign_keys=[processed_by_employee_id],
    )

    document_type_info = relationship(
        "HRDocumentType",
        back_populates="document_requests",
        foreign_keys=[document_type],
    )

    history = relationship(
        "HRDocumentRequestHistory",
        back_populates="document_request",
    )