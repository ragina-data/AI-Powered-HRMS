from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class HRPolicyVersion(Base):
    __tablename__ = "hr_policy_versions"

    policy_version_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    policy_id = Column(
        BigInteger,
        ForeignKey(
            "hr_policies.policy_id",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    version_number = Column(
        Integer,
        nullable=False,
    )

    version_label = Column(
        String(50),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        server_default=text("'draft'"),
    )

    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_by_user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
        nullable=True,
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_file_name = Column(
        String(500),
        nullable=True,
    )

    source_reference = Column(
        Text,
        nullable=True,
    )

    change_summary = Column(
        Text,
        nullable=True,
    )

    created_by_user_id = Column(
        BigInteger,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
            onupdate="NO ACTION",
        ),
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

    policy = relationship("HRPolicy")

    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )

    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )

    chunks = relationship(
    "HRPolicyChunk",
    back_populates="policy_version",
)