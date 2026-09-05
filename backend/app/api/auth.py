from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SessionData, get_session_data, require_account
from app.core.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    sign_session,
    verify_password,
)
from app.db import get_session
from app.models.account import Account
from app.models.shop import Shop
from app.schemas.auth import LoginRequest, MeResponse

router = APIRouter(tags=["auth"])

WRONG_CREDENTIALS = "نام کاربری یا رمز درست نیست."


@router.post("/auth/login")
async def login(
    body: LoginRequest, response: Response, db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(Account).where(Account.username == body.username))
    account = result.scalar_one_or_none()
    if account is None or not account.is_active or not verify_password(
        body.password, account.password_hash
    ):
        raise HTTPException(status_code=401, detail=WRONG_CREDENTIALS)

    token = sign_session({"account_id": account.id, "role": account.role})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True}


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(
    account: Account = Depends(require_account),
    session_data: SessionData = Depends(get_session_data),
    db: AsyncSession = Depends(get_session),
):
    shop_id = None
    shop_name = None
    if account.role == "seller":
        result = await db.execute(select(Shop).where(Shop.account_id == account.id))
        shop = result.scalar_one_or_none()
        if shop:
            shop_id, shop_name = shop.id, shop.name

    acting_as_shop_id = None
    acting_as_shop_name = None
    if account.role == "operator" and session_data and session_data.acting_as_shop_id:
        shop = await db.get(Shop, session_data.acting_as_shop_id)
        if shop:
            acting_as_shop_id, acting_as_shop_name = shop.id, shop.name

    return MeResponse(
        account_id=account.id,
        username=account.username,
        role=account.role,
        shop_id=shop_id,
        shop_name=shop_name,
        acting_as_shop_id=acting_as_shop_id,
        acting_as_shop_name=acting_as_shop_name,
    )
