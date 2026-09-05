from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"))
    name: Mapped[str] = mapped_column(String(128))
    garment_type_id: Mapped[int] = mapped_column(ForeignKey("garment_types.id"))
    numbers_kind: Mapped[str] = mapped_column(String(16))  # circumference | width
    link_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    shop_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ProductSize(Base):
    __tablename__ = "product_sizes"
    __table_args__ = (UniqueConstraint("product_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SizeMeasurement(Base):
    __tablename__ = "size_measurements"
    __table_args__ = (UniqueConstraint("product_size_id", "criterion_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_size_id: Mapped[int] = mapped_column(ForeignKey("product_sizes.id"))
    criterion_id: Mapped[int] = mapped_column(ForeignKey("measurement_criteria.id"))
    value_cm: Mapped[float] = mapped_column(Numeric(5, 1))
