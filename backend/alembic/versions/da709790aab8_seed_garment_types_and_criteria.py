"""seed garment types and criteria

Revision ID: da709790aab8
Revises: 7be5beac88bb
Create Date: 2026-09-05 15:05:29.549803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da709790aab8'
down_revision: Union[str, None] = '7be5beac88bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

garment_types_table = sa.table(
    "garment_types",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("is_active", sa.Boolean),
)

criteria_table = sa.table(
    "measurement_criteria",
    sa.column("id", sa.Integer),
    sa.column("garment_type_id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("is_main", sa.Boolean),
    sa.column("kind", sa.String),
    sa.column("where_text", sa.String),
    sa.column("measure_rule", sa.String),
    sa.column("sort_order", sa.Integer),
)

TOP_ID = 1
BOTTOM_ID = 2

TOP_CRITERIA = [
    dict(name="دورِ سینه", is_main=True, kind="circumference",
         where_text="۱ سانت زیرِ بغل، از این طرف تا آن طرف",
         measure_rule="chest_width", sort_order=1),
    dict(name="طولِ لباس", is_main=True, kind="length",
         where_text="از بالای شانه تا پایینِ لباس",
         measure_rule="garment_length", sort_order=2),
    dict(name="عرضِ شانه", is_main=False, kind="length",
         where_text="از سرِ یک شانه تا سرِ شانهٔ دیگر",
         measure_rule="shoulder_width", sort_order=3),
    dict(name="طولِ آستین", is_main=False, kind="length",
         where_text="از سرِ شانه تا نوکِ آستین",
         measure_rule="sleeve_length", sort_order=4),
    dict(name="دورِ بازو", is_main=False, kind="circumference",
         where_text="پهن‌ترینِ قسمتِ آستین",
         measure_rule="bicep_width", sort_order=5),
    dict(name="دورِ کمرِ لباس", is_main=False, kind="circumference",
         where_text="باریک‌ترین قسمتِ بدنهٔ لباس بینِ سینه و پایین",
         measure_rule="garment_waist_width", sort_order=6),
]

BOTTOM_CRITERIA = [
    dict(name="دورِ کمر", is_main=True, kind="circumference",
         where_text="لبهٔ بالای شلوار، از این طرف تا آن طرف",
         measure_rule="waist_width", sort_order=1),
    dict(name="قد", is_main=True, kind="length",
         where_text="از لبهٔ بالای شلوار تا پایینِ پاچه",
         measure_rule="bottom_length", sort_order=2),
    dict(name="دورِ باسن", is_main=False, kind="circumference",
         where_text="پهن‌ترینِ قسمتِ بالای شلوار",
         measure_rule="hip_width", sort_order=3),
    dict(name="دورِ ران", is_main=False, kind="circumference",
         where_text="۲ سانت زیرِ چاک، پهن‌ترینِ قسمتِ ران",
         measure_rule="thigh_width", sort_order=4),
    dict(name="دورِ دمِ پا", is_main=False, kind="circumference",
         where_text="لبهٔ پایینِ پاچه",
         measure_rule="leg_opening_width", sort_order=5),
    dict(name="فاق", is_main=False, kind="length",
         where_text="از لبهٔ بالای شلوار تا نقطهٔ چاک",
         measure_rule="rise", sort_order=6),
]


def upgrade() -> None:
    op.bulk_insert(
        garment_types_table,
        [
            {"id": TOP_ID, "name": "بالاتنه", "is_active": True},
            {"id": BOTTOM_ID, "name": "پایین‌تنه", "is_active": True},
        ],
    )
    rows = []
    for c in TOP_CRITERIA:
        rows.append({**c, "garment_type_id": TOP_ID})
    for c in BOTTOM_CRITERIA:
        rows.append({**c, "garment_type_id": BOTTOM_ID})
    op.bulk_insert(criteria_table, rows)


def downgrade() -> None:
    op.execute(criteria_table.delete())
    op.execute(garment_types_table.delete())
