from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GarmentType(Base):
    __tablename__ = "garment_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MeasurementCriterion(Base):
    __tablename__ = "measurement_criteria"
    __table_args__ = (UniqueConstraint("garment_type_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    garment_type_id: Mapped[int] = mapped_column(ForeignKey("garment_types.id"))
    name: Mapped[str] = mapped_column(String(64))
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    kind: Mapped[str] = mapped_column(String(16))  # circumference | length
    where_text: Mapped[str] = mapped_column(String(255))
    measure_rule: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
