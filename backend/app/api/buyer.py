import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codes import new_code
from app.core.storage import LocalStorage
from app.core.throttle import is_rate_limited
from app.db import get_session
from app.measure.ingest import UploadTooLarge, encode_jpeg, load_upright_rgb
from app.measure.pipeline import Criterion as PipelineCriterion
from app.measure.pipeline import run_pipeline_sync
from app.models.garment import MeasurementCriterion
from app.models.job import Job
from app.models.product import Product, ProductSize, SizeMeasurement
from app.models.request import ExtractedMeasurement, MeasureRequest
from app.models.shop import Shop
from app.sizing.compare import CriterionInfo, SizeChart, compute_answer
from app.sizing.normalise import normalise_value

router = APIRouter(tags=["buyer"])

REJECT_MESSAGES = {
    "blurry": "عکس تار است",
    "card_not_found": "کارت را در عکس پیدا نکردیم",
    "garment_cropped": "قسمتی از لباس بیرونِ قاب است",
}

PHOTO_TTL_MINUTES = 30
storage = LocalStorage()


def _as_utc(dt: datetime) -> datetime:
    # SQLite drops tzinfo even on a DateTime(timezone=True) column
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def _get_active_product(link_code: str, db: AsyncSession) -> tuple[Product, Shop]:
    result = await db.execute(select(Product).where(Product.link_code == link_code))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    shop = await db.get(Shop, product.shop_id)
    if shop is None or not shop.is_active or not product.is_active:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    return product, shop


@router.get("/p/{link_code}")
async def get_product_public(link_code: str, db: AsyncSession = Depends(get_session)):
    product, shop = await _get_active_product(link_code, db)
    return {
        "shop_name": shop.name,
        "product_name": product.name,
        "photo_url": None,
        "is_active": product.is_active,
    }


async def _load_criteria(garment_type_id: int, db: AsyncSession) -> list[MeasurementCriterion]:
    result = await db.execute(
        select(MeasurementCriterion).where(MeasurementCriterion.garment_type_id == garment_type_id)
    )
    return list(result.scalars().all())


@router.post("/p/{link_code}/measure")
async def measure(
    link_code: str, request: Request, photo: UploadFile, db: AsyncSession = Depends(get_session)
):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="درخواست‌های زیاد. کمی بعد دوباره امتحان کن.")

    product, shop = await _get_active_product(link_code, db)

    data = await photo.read()
    try:
        rgb = load_upright_rgb(data)
    except UploadTooLarge:
        raise HTTPException(status_code=400, detail="عکس خیلی حجیم است")
    except Exception:
        raise HTTPException(status_code=400, detail="عکس خوانده نشد")

    normalised_jpeg = encode_jpeg(rgb)
    criteria = await _load_criteria(product.garment_type_id, db)
    pipeline_criteria = [
        PipelineCriterion(id=c.id, kind=c.kind, measure_rule=c.measure_rule) for c in criteria
    ]

    now = datetime.now(timezone.utc)
    result = await asyncio.to_thread(run_pipeline_sync, normalised_jpeg, pipeline_criteria)

    view_code = new_code()

    if result["status"] == "rejected":
        request = MeasureRequest(
            product_id=product.id,
            created_at=now,
            status="rejected",
            reject_reason=result["reason"],
            photo_path=None,
            photo_delete_at=now,  # nothing to delete; photo is never persisted on rejection
            view_code=view_code,
        )
        db.add(request)
        await db.commit()
        return {
            "status": "rejected",
            "reason": result["reason"],
            "message": REJECT_MESSAGES.get(result["reason"], "عکس پذیرفته نشد"),
        }

    # measured: build the seller's chart, normalised to circumference, and compare
    sizes_rows = (
        await db.execute(select(ProductSize).where(ProductSize.product_id == product.id))
    ).scalars().all()
    measurements_rows = (
        await db.execute(
            select(SizeMeasurement).where(
                SizeMeasurement.product_size_id.in_([s.id for s in sizes_rows])
            )
        )
    ).scalars().all() if sizes_rows else []

    criteria_by_id = {c.id: c for c in criteria}
    size_values: dict[int, dict[int, float]] = {s.id: {} for s in sizes_rows}
    for m in measurements_rows:
        c = criteria_by_id.get(m.criterion_id)
        if c is None:
            continue
        size_values[m.product_size_id][m.criterion_id] = normalise_value(
            float(m.value_cm), c.kind, product.numbers_kind
        )

    size_charts = [SizeChart(id=s.id, name=s.name, values=size_values[s.id]) for s in sizes_rows]
    criteria_info = [
        CriterionInfo(id=c.id, name=c.name, kind=c.kind, is_main=c.is_main) for c in criteria
    ]

    answer = compute_answer(result["values"], size_charts, criteria_info)

    photo_delete_at = now + timedelta(minutes=PHOTO_TTL_MINUTES)
    photo_key = storage.save(normalised_jpeg, ".jpg")

    recommended_size_id = None
    if answer["status"] == "answered":
        recommended_size_id = answer["recommended_size"]["id"]

    request = MeasureRequest(
        product_id=product.id,
        created_at=now,
        status="answered",
        reject_reason=None,
        recommended_size_id=recommended_size_id,
        photo_path=photo_key,
        photo_delete_at=photo_delete_at,
        view_code=view_code,
    )
    db.add(request)
    await db.flush()

    for criterion_id, value_cm in result["values"].items():
        db.add(
            ExtractedMeasurement(request_id=request.id, criterion_id=criterion_id, value_cm=value_cm)
        )

    db.add(
        Job(
            kind="delete_photo",
            run_at=photo_delete_at,
            payload={"request_id": request.id},
        )
    )
    await db.commit()

    return {"status": "answered", "view_code": view_code}


@router.get("/r/{view_code}")
async def get_answer(view_code: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(MeasureRequest).where(MeasureRequest.view_code == view_code))
    request = result.scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")

    now = datetime.now(timezone.utc)
    if now >= _as_utc(request.photo_delete_at):
        raise HTTPException(status_code=410, detail="این جواب پاک شده")

    product = await db.get(Product, request.product_id)
    shop = await db.get(Shop, product.shop_id) if product else None
    criteria = await _load_criteria(product.garment_type_id, db) if product else []
    criteria_by_id = {c.id: c for c in criteria}

    extracted = (
        await db.execute(
            select(ExtractedMeasurement).where(ExtractedMeasurement.request_id == request.id)
        )
    ).scalars().all()
    buyer_values = {e.criterion_id: float(e.value_cm) for e in extracted}

    sizes_rows = (
        await db.execute(select(ProductSize).where(ProductSize.product_id == product.id))
    ).scalars().all() if product else []
    measurements_rows = (
        await db.execute(
            select(SizeMeasurement).where(
                SizeMeasurement.product_size_id.in_([s.id for s in sizes_rows])
            )
        )
    ).scalars().all() if sizes_rows else []

    size_values: dict[int, dict[int, float]] = {s.id: {} for s in sizes_rows}
    for m in measurements_rows:
        c = criteria_by_id.get(m.criterion_id)
        if c is None:
            continue
        size_values[m.product_size_id][m.criterion_id] = normalise_value(
            float(m.value_cm), c.kind, product.numbers_kind
        )

    size_charts = [SizeChart(id=s.id, name=s.name, values=size_values[s.id]) for s in sizes_rows]
    criteria_info = [
        CriterionInfo(id=c.id, name=c.name, kind=c.kind, is_main=c.is_main) for c in criteria
    ]
    answer = compute_answer(buyer_values, size_charts, criteria_info)

    return {
        **answer,
        "shop_name": shop.name if shop else "",
        "product_name": product.name if product else "",
        "shop_url": product.shop_url if product else None,
    }
