from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codes import new_code
from app.core.deps import require_current_shop
from app.db import get_session
from app.models.garment import MeasurementCriterion
from app.models.product import Product, ProductSize, SizeMeasurement
from app.models.request import MeasureRequest
from app.models.shop import Shop
from app.schemas.product import (
    MeasurementUpsert,
    NumbersKindSwitch,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    SizeCreate,
    SizeOut,
)

router = APIRouter(tags=["seller"])


async def _get_owned_product(product_id: int, shop: Shop, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    return product


async def _main_criterion_ids(garment_type_id: int, db: AsyncSession) -> set[int]:
    result = await db.execute(
        select(MeasurementCriterion.id).where(
            MeasurementCriterion.garment_type_id == garment_type_id,
            MeasurementCriterion.is_main.is_(True),
        )
    )
    return set(result.scalars().all())


async def _size_is_complete(size_id: int, main_ids: set[int], db: AsyncSession) -> bool:
    if not main_ids:
        return True
    result = await db.execute(
        select(SizeMeasurement.criterion_id).where(
            SizeMeasurement.product_size_id == size_id,
            SizeMeasurement.criterion_id.in_(main_ids),
        )
    )
    have = set(result.scalars().all())
    return main_ids.issubset(have)


async def product_is_complete(product: Product, db: AsyncSession) -> tuple[bool, int, int]:
    """Returns (all_complete, complete_count, total_count) for a product's sizes."""
    main_ids = await _main_criterion_ids(product.garment_type_id, db)
    sizes = (
        await db.execute(select(ProductSize).where(ProductSize.product_id == product.id))
    ).scalars().all()
    if not sizes:
        return False, 0, 0
    complete = 0
    for s in sizes:
        if await _size_is_complete(s.id, main_ids, db):
            complete += 1
    return complete == len(sizes), complete, len(sizes)


@router.get("/products", response_model=list[ProductOut])
async def list_products(shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Product).where(Product.shop_id == shop.id))
    return result.scalars().all()


@router.post("/products", response_model=ProductOut)
async def create_product(
    body: ProductCreate,
    shop: Shop = Depends(require_current_shop),
    db: AsyncSession = Depends(get_session),
):
    if body.numbers_kind not in ("circumference", "width"):
        raise HTTPException(status_code=400, detail="نوعِ اعداد نامعتبر است")
    product = Product(
        shop_id=shop.id,
        name=body.name,
        garment_type_id=body.garment_type_id,
        numbers_kind=body.numbers_kind,
        link_code=new_code(),
        shop_url=body.shop_url,
        is_active=False,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    return await _get_owned_product(product_id, shop, db)


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    shop: Shop = Depends(require_current_shop),
    db: AsyncSession = Depends(get_session),
):
    product = await _get_owned_product(product_id, shop, db)
    if body.name is not None:
        product.name = body.name
    if body.shop_url is not None:
        product.shop_url = body.shop_url
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/products/{product_id}/deactivate")
async def deactivate_product(product_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    product = await _get_owned_product(product_id, shop, db)
    product.is_active = False
    await db.commit()
    return {"ok": True}


@router.post("/products/{product_id}/numbers-kind", response_model=ProductOut)
async def switch_numbers_kind(
    product_id: int,
    body: NumbersKindSwitch,
    shop: Shop = Depends(require_current_shop),
    db: AsyncSession = Depends(get_session),
):
    product = await _get_owned_product(product_id, shop, db)
    if body.numbers_kind not in ("circumference", "width"):
        raise HTTPException(status_code=400, detail="نوعِ اعداد نامعتبر است")
    if body.numbers_kind == product.numbers_kind:
        return product
    if not body.confirm:
        raise HTTPException(
            status_code=409,
            detail="این کار همهٔ اندازه‌های ثبت‌شده را خالی می‌کند. برای ادامه تأیید کن.",
        )
    sizes = (await db.execute(select(ProductSize).where(ProductSize.product_id == product.id))).scalars().all()
    size_ids = [s.id for s in sizes]
    if size_ids:
        await db.execute(
            SizeMeasurement.__table__.delete().where(SizeMeasurement.product_size_id.in_(size_ids))
        )
    product.numbers_kind = body.numbers_kind
    product.is_active = False
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/products/{product_id}/sizes", response_model=list[SizeOut])
async def list_sizes(product_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    product = await _get_owned_product(product_id, shop, db)
    main_ids = await _main_criterion_ids(product.garment_type_id, db)
    sizes = (
        await db.execute(
            select(ProductSize).where(ProductSize.product_id == product.id).order_by(ProductSize.sort_order)
        )
    ).scalars().all()
    out = []
    for s in sizes:
        measurements = (
            await db.execute(select(SizeMeasurement).where(SizeMeasurement.product_size_id == s.id))
        ).scalars().all()
        m = {mm.criterion_id: float(mm.value_cm) for mm in measurements}
        complete = await _size_is_complete(s.id, main_ids, db)
        out.append(SizeOut(id=s.id, name=s.name, sort_order=s.sort_order, is_complete=complete, measurements=m))
    return out


@router.post("/products/{product_id}/sizes", response_model=SizeOut)
async def add_size(
    product_id: int,
    body: SizeCreate,
    shop: Shop = Depends(require_current_shop),
    db: AsyncSession = Depends(get_session),
):
    product = await _get_owned_product(product_id, shop, db)
    max_sort = (
        await db.execute(
            select(ProductSize.sort_order)
            .where(ProductSize.product_id == product.id)
            .order_by(ProductSize.sort_order.desc())
            .limit(1)
        )
    ).scalar_one_or_none() or 0
    size = ProductSize(product_id=product.id, name=body.name, sort_order=max_sort + 1)
    db.add(size)
    await db.commit()
    await db.refresh(size)
    return SizeOut(id=size.id, name=size.name, sort_order=size.sort_order, is_complete=False, measurements={})


@router.delete("/sizes/{size_id}")
async def delete_size(size_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    size = await db.get(ProductSize, size_id)
    if size is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    product = await db.get(Product, size.product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="پیدا نشد")

    has_requests = (
        await db.execute(select(MeasureRequest).where(MeasureRequest.recommended_size_id == size_id).limit(1))
    ).scalar_one_or_none()
    if has_requests is not None:
        raise HTTPException(
            status_code=409, detail="این سایز درخواستِ گذشته دارد. برای حذف دوباره تأیید کن."
        )

    await db.execute(SizeMeasurement.__table__.delete().where(SizeMeasurement.product_size_id == size_id))
    await db.delete(size)
    await db.commit()
    return {"ok": True}


@router.delete("/sizes/{size_id}/force")
async def force_delete_size(size_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    size = await db.get(ProductSize, size_id)
    if size is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    product = await db.get(Product, size.product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    await db.execute(SizeMeasurement.__table__.delete().where(SizeMeasurement.product_size_id == size_id))
    await db.execute(
        MeasureRequest.__table__.update()
        .where(MeasureRequest.recommended_size_id == size_id)
        .values(recommended_size_id=None)
    )
    await db.delete(size)
    await db.commit()
    return {"ok": True}


@router.put("/sizes/{size_id}/measurements")
async def upsert_measurement(
    size_id: int,
    body: MeasurementUpsert,
    shop: Shop = Depends(require_current_shop),
    db: AsyncSession = Depends(get_session),
):
    if body.value_cm <= 0:
        raise HTTPException(status_code=400, detail="عدد باید مثبت باشد")
    size = await db.get(ProductSize, size_id)
    if size is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    product = await db.get(Product, size.product_id)
    if product is None or product.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="پیدا نشد")

    existing = (
        await db.execute(
            select(SizeMeasurement).where(
                SizeMeasurement.product_size_id == size_id,
                SizeMeasurement.criterion_id == body.criterion_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.value_cm = body.value_cm
    else:
        db.add(SizeMeasurement(product_size_id=size_id, criterion_id=body.criterion_id, value_cm=body.value_cm))
    await db.commit()

    # first activation gate: link goes live only when every size is complete (decision 49)
    if not product.is_active:
        all_complete, complete_count, total = await product_is_complete(product, db)
        if all_complete and total > 0:
            product.is_active = True
            await db.commit()

    return {"ok": True}


@router.get("/products/{product_id}/link")
async def get_link(product_id: int, shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    product = await _get_owned_product(product_id, shop, db)
    all_complete, complete_count, total = await product_is_complete(product, db)
    return {
        "link_code": product.link_code,
        "is_active": product.is_active,
        "complete_count": complete_count,
        "total_count": total,
    }


@router.get("/requests")
async def list_requests(shop: Shop = Depends(require_current_shop), db: AsyncSession = Depends(get_session)):
    products = (await db.execute(select(Product.id, Product.name).where(Product.shop_id == shop.id))).all()
    product_ids = [p.id for p in products]
    names = {p.id: p.name for p in products}
    if not product_ids:
        return {"requests": [], "answered_count": 0, "rejected_count": 0}

    requests = (
        await db.execute(
            select(MeasureRequest)
            .where(MeasureRequest.product_id.in_(product_ids))
            .order_by(MeasureRequest.created_at.desc())
        )
    ).scalars().all()

    size_names: dict[int, str] = {}
    size_ids = [r.recommended_size_id for r in requests if r.recommended_size_id]
    if size_ids:
        sizes = (await db.execute(select(ProductSize).where(ProductSize.id.in_(size_ids)))).scalars().all()
        size_names = {s.id: s.name for s in sizes}

    answered = sum(1 for r in requests if r.status == "answered")
    rejected = sum(1 for r in requests if r.status == "rejected")

    return {
        "requests": [
            {
                "id": r.id,
                "product_name": names.get(r.product_id, ""),
                "created_at": r.created_at.isoformat(),
                "status": r.status,
                "recommended_size_name": size_names.get(r.recommended_size_id) if r.recommended_size_id else None,
                "reject_reason": r.reject_reason,
            }
            for r in requests
        ],
        "answered_count": answered,
        "rejected_count": rejected,
    }
