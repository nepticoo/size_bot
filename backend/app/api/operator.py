import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_operator
from app.core.security import SESSION_COOKIE, hash_password, sign_session
from app.db import get_session
from app.models.account import Account
from app.models.shop import Shop
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
