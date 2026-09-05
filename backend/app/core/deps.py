from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SESSION_COOKIE, verify_session
from app.db import get_session
from app.models.account import Account
from app.models.shop import Shop


class SessionData:
    def __init__(self, account_id: int, role: str, acting_as_shop_id: int | None):
        self.account_id = account_id
        self.role = role
        self.acting_as_shop_id = acting_as_shop_id


async def get_session_data(request: Request) -> SessionData | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    data = verify_session(token)
    if not data:
        return None
    return SessionData(
        account_id=data["account_id"],
        role=data["role"],
        acting_as_shop_id=data.get("acting_as_shop_id"),
    )


async def require_account(
    session_data: SessionData | None = Depends(get_session_data),
    db: AsyncSession = Depends(get_session),
) -> Account:
    if session_data is None:
        raise HTTPException(status_code=401, detail="وارد نشده‌ای")
    account = await db.get(Account, session_data.account_id)
    if account is None or not account.is_active:
        raise HTTPException(status_code=401, detail="وارد نشده‌ای")
    account._session = session_data  # stash for downstream deps
    return account


async def require_current_shop(
    account: Account = Depends(require_account),
    db: AsyncSession = Depends(get_session),
) -> Shop:
    """Resolves 'the current shop' per architecture.md's rule:
    - seller -> their own shop, always (acting_as_shop_id is ignored/unsettable)
    - operator with acting_as_shop_id -> that shop
    - operator without it -> 403
    """
    session_data: SessionData = account._session
    if account.role == "seller":
        result = await db.execute(select(Shop).where(Shop.account_id == account.id))
        shop = result.scalar_one_or_none()
        if shop is None:
            raise HTTPException(status_code=403, detail="فروشگاهی برای این حساب نیست")
        return shop
    if account.role == "operator":
        if not session_data.acting_as_shop_id:
            raise HTTPException(status_code=403, detail="دسترسی ندارید")
        shop = await db.get(Shop, session_data.acting_as_shop_id)
        if shop is None:
            raise HTTPException(status_code=403, detail="دسترسی ندارید")
        return shop
    raise HTTPException(status_code=403, detail="دسترسی ندارید")


async def require_operator(account: Account = Depends(require_account)) -> Account:
    if account.role != "operator":
        raise HTTPException(status_code=403, detail="دسترسی ندارید")
    return account
