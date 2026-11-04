from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class LeaveEntitlementRule(Base):
    __tablename__ = "leave_entitlement_rules"

    entitlement_rule_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    leave_type_id = Column(
        BigInteger,
        ForeignKey(
            "leave_types.leave_type_id",
            ondelete="NO ACTION",
            onupdate="NO ACTION",
        ),
        nullable=False,
    )

    employment_category = Column(
        String(50),
        nullable=False,
        server_default=text("'all'"),
    )

    entitlement_days = Column(
        Numeric,
        nullable=False,
    )

    effective_from = Column(
        Date,
        nullable=False,
    )

    effective_to = Column(
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

    leave_type = relationship(
        "LeaveType",
        back_populates="entitlement_rules",
    )