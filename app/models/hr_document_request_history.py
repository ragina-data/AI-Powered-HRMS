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


class HRDocumentRequestHistory(Base):
    __tablename__ = "hr_document_request_history"

    history_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    document_request_id = Column(
        BigInteger,
        ForeignKey(
            "hr_document_requests.document_request_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    previous_status = Column(
        String(20),
        nullable=True,
    )

    new_status = Column(
        String(20),
        nullable=False,
    )

    action_by_user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    comments = Column(
        Text,
        nullable=True,
    )

    action_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    document_request = relationship(
        "HRDocumentRequest",
        back_populates="history",
    )

    action_by_user = relationship("User")