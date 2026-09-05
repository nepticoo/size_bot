from app.core.security import hash_password
from app.models.account import Account


async def make_account(db_session, username="nakhonaghsh", password="rightpass", role="seller"):
    account = Account(
        username=username, password_hash=hash_password(password), role=role, is_active=True
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


async def test_wrong_username_and_wrong_password_give_identical_error(client, db_session):
    await make_account(db_session)

    r1 = await client.post("/api/auth/login", json={"username": "nope", "password": "x"})
    r2 = await client.post(
        "/api/auth/login", json={"username": "nakhonaghsh", "password": "wrong"}
    )
    assert r1.status_code == 401
    assert r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


async def test_correct_login_then_me(client, db_session):
    await make_account(db_session)
    r = await client.post(
        "/api/auth/login", json={"username": "nakhonaghsh", "password": "rightpass"}
    )
    assert r.status_code == 200

    r2 = await client.get("/api/me")
    assert r2.status_code == 200
    assert r2.json()["username"] == "nakhonaghsh"


async def test_logout_then_me_requires_login(client, db_session):
    await make_account(db_session)
    await client.post("/api/auth/login", json={"username": "nakhonaghsh", "password": "rightpass"})
    await client.post("/api/auth/logout")
    r = await client.get("/api/me")
    assert r.status_code == 401
