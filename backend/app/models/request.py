from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MeasureRequest(Base):
    __tablename__ = "measure_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[str] = mapped_column(String(16))  # processing | answered | rejected
    reject_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recommended_size_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_sizes.id"), nullable=True
    )
    photo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_delete_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    view_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)


class ExtractedMeasurement(Base):
    __tablename__ = "extracted_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("measure_requests.id"))
    criterion_id: Mapped[int] = mapped_column(ForeignKey("measurement_criteria.id"))
    value_cm: Mapped[float] = mapped_column(Numeric(5, 1))
