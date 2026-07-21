from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from backend.database.connection import Base


class BrandAnalysis(Base):
    __tablename__ = "brand_analyses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    product_description: Mapped[str] = mapped_column(
        Text,
    )

    target_market: Mapped[str] = mapped_column(
        String(255),
    )

    overall_score: Mapped[float] = mapped_column(
        Float,
    )

    rejected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    report_path: Mapped[str] = mapped_column(
        Text,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )