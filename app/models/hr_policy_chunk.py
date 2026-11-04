from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import HALFVEC

from app.db.session import Base


class HRPolicyChunk(Base):
    __tablename__ = "hr_policy_chunks"

    policy_chunk_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    policy_version_id = Column(
        BigInteger,
        ForeignKey(
            "hr_policy_versions.policy_version_id",
            ondelete="RESTRICT",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    chunk_number = Column(
        Integer,
        nullable=False,
    )

    section_heading = Column(
        String(500),
        nullable=True,
    )

    chunk_text = Column(
        Text,
        nullable=False,
    )

    page_number = Column(
        Integer,
        nullable=True,
    )

    source_reference = Column(
        Text,
        nullable=True,
    )

    embedding_model = Column(
        String(100),
        nullable=False,
        server_default=text("'gemini-embedding-001'"),
    )

    embedding_dimensions = Column(
        SmallInteger,
        nullable=False,
        server_default=text("3072"),
    )

    embedding = Column(
        HALFVEC(3072),
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

    search_vector = Column(
        TSVECTOR,
        nullable=True,
    )

    policy_version = relationship(
        "HRPolicyVersion",
        back_populates="chunks",
    )