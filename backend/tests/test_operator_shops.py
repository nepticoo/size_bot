from app.core.security import hash_password
from app.models.account import Account


async def make_operator(db_session, username="admin", password="adminpass"):
    account = Account(
        username=username, password_hash=hash_password(password), role="operator", is_active=True
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


async def login_operator(client, db_session):
    await make_operator(db_session)
    await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})


async def test_create_shop_returns_password_in_clear(client, db_session):
    await login_operator(client, db_session)
    r = await client.post(
        "/api/admin/shops",
        json={"name": "کاوان استایل", "username": "kavan.style", "instagram": "@kavan.style", "phone": "09027778899"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "kavan.style"
    assert len(body["password"]) >= 8

    # log in with the returned credentials to prove they work
    r2 = await client.post(
        "/api/auth/login", json={"username": "kavan.style", "password": body["password"]}
    )
    assert r2.status_code == 200


async def test_duplicate_username_rejected(client, db_session):
    await login_operator(client, db_session)
    await client.post(
        "/api/admin/shops",
        json={"name": "نخ و نقش", "username": "nakhonaghsh", "instagram": "@nakhonaghsh"},
    )
    r = await client.post(
        "/api/admin/shops",
        json={"name": "شاپِ دیگر", "username": "nakhonaghsh"},
    )
    assert r.status_code == 409
