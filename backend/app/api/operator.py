import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_operator
from app.core.security import SESSION_COOKIE, hash_password, sign_session
from app.db import get_session
from app.models.account import Account
from app.models.garment import GarmentType, MeasurementCriterion
from app.models.shop import Shop
from app.schemas.criterion import CriterionCreate, CriterionOut
from app.schemas.shop import ShopCreate, ShopCreateResult, ShopOut

router = APIRouter(tags=["operator"], dependencies=[Depends(require_operator)])


def _generate_password() -> str:
    return secrets.token_urlsafe(9)


@router.get("/admin/shops")
async def list_shops(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Shop, Account).join(Account, Shop.account_id == Account.id))
    return [
        {
            "id": shop.id,
            "name": shop.name,
            "instagram": shop.instagram,
            "phone": shop.phone,
            "is_active": shop.is_active,
            "username": account.username,
        }
        for shop, account in result.all()
    ]


@router.post("/admin/shops", response_model=ShopCreateResult)
async def create_shop(body: ShopCreate, db: AsyncSession = Depends(get_session)):
    existing = await db.execute(select(Account).where(Account.username == body.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="این نام کاربری قبلاً استفاده شده است.")

    password = _generate_password()
    account = Account(
        username=body.username,
        password_hash=hash_password(password),
        role="seller",
        is_active=True,
    )
    db.add(account)
    await db.flush()

    shop = Shop(
        name=body.name,
        instagram=body.instagram,
        phone=body.phone,
        is_active=True,
        account_id=account.id,
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)

    return ShopCreateResult(
        shop=ShopOut(
            id=shop.id,
            name=shop.name,
            instagram=shop.instagram,
            phone=shop.phone,
            is_active=shop.is_active,
            username=account.username,
        ),
        username=account.username,
        password=password,
    )


@router.post("/admin/shops/{shop_id}/deactivate")
async def deactivate_shop(shop_id: int, db: AsyncSession = Depends(get_session)):
    shop = await db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    account = await db.get(Account, shop.account_id)
    shop.is_active = False
    if account:
        account.is_active = False
    await db.commit()
    return {"ok": True}


@router.post("/admin/shops/{shop_id}/impersonate")
async def impersonate(shop_id: int, operator: Account = Depends(require_operator), db: AsyncSession = Depends(get_session)):
    shop = await db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="پیدا نشد")
    token = sign_session(
        {"account_id": operator.id, "role": operator.role, "acting_as_shop_id": shop.id}
    )
    response = Response()
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax")
    return response


@router.get("/admin/criteria", response_model=list[CriterionOut])
async def list_criteria(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(MeasurementCriterion).order_by(
            MeasurementCriterion.garment_type_id, MeasurementCriterion.sort_order
        )
    )
    return result.scalars().all()


@router.post("/admin/criteria", response_model=CriterionOut)
async def create_criterion(body: CriterionCreate, db: AsyncSession = Depends(get_session)):
    garment_type = await db.get(GarmentType, body.garment_type_id)
    if garment_type is None:
        raise HTTPException(status_code=404, detail="نوعِ پوشاک پیدا نشد")

    existing = await db.execute(
        select(MeasurementCriterion).where(
            MeasurementCriterion.garment_type_id == body.garment_type_id,
            MeasurementCriterion.name == body.name,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="این معیار برای این نوعِ پوشاک تکراری است.")

    max_sort = await db.execute(
        select(MeasurementCriterion.sort_order)
        .where(MeasurementCriterion.garment_type_id == body.garment_type_id)
        .order_by(MeasurementCriterion.sort_order.desc())
        .limit(1)
    )
    next_sort = (max_sort.scalar_one_or_none() or 0) + 1

    criterion = MeasurementCriterion(
        garment_type_id=body.garment_type_id,
        name=body.name,
        is_main=body.is_main,
        kind=body.kind,
        where_text=body.where_text,
        measure_rule=body.measure_rule,
        sort_order=next_sort,
    )
    db.add(criterion)
    await db.commit()
    await db.refresh(criterion)
    return criterion
