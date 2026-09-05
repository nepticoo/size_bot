from app.core.security import hash_password
from app.models.account import Account
from app.models.shop import Shop


async def make_operator(db_session, username="admin", password="adminpass"):
    account = Account(username=username, password_hash=hash_password(password), role="operator", is_active=True)
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


async def make_seller_shop(db_session, username="nakhonaghsh", password="p", name="نخ و نقش"):
    account = Account(username=username, password_hash=hash_password(password), role="seller", is_active=True)
    db_session.add(account)
    await db_session.flush()
    shop = Shop(name=name, is_active=True, account_id=account.id)
    db_session.add(shop)
    await db_session.commit()
    await db_session.refresh(shop)
    return shop, account


async def test_operator_can_impersonate_and_seller_cannot(client, db_session):
    await make_operator(db_session)
    shop, seller_account = await make_seller_shop(db_session)

    await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    r = await client.post(f"/api/admin/shops/{shop.id}/impersonate")
    assert r.status_code == 200

    me = await client.get("/api/me")
    assert me.json()["acting_as_shop_id"] == shop.id

    # a seller session can never set acting_as_shop_id
    await client.post("/api/auth/logout")
    await client.post("/api/auth/login", json={"username": "nakhonaghsh", "password": "p"})
    r2 = await client.post(f"/api/admin/shops/{shop.id}/impersonate")
    assert r2.status_code == 403


async def test_deactivated_shop_stops_answering(client, db_session):
    await make_operator(db_session)
    shop, _ = await make_seller_shop(db_session)
    await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    r = await client.post(f"/api/admin/shops/{shop.id}/deactivate")
    assert r.status_code == 200
    await db_session.refresh(shop)
    assert shop.is_active is False
