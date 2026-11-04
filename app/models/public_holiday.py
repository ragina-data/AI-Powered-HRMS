from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    String,
    text,
)


from app.db.session import Base


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    public_holiday_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    holiday_date = Column(
        Date,
        nullable=False,
    )

    holiday_name = Column(
        String(150),
        nullable=False,
    )

    country_code = Column(
        String(2),
        nullable=False,
        server_default=text("'AE'"),
    )

    region = Column(
        String(100),
        nullable=False,
        server_default=text("'all'"),
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