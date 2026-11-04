from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class HRDocumentType(Base):
    __tablename__ = "hr_document_types"

    document_type_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    document_type_code = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    document_type_name = Column(
        String(120),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    requires_hr_approval = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
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

    document_requests = relationship(
        "HRDocumentRequest",
        back_populates="document_type_info",
    )