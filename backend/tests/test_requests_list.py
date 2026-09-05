from datetime import datetime, timezone

from app.core.security import hash_password
from app.models.account import Account
from app.models.garment import GarmentType, MeasurementCriterion
from app.models.product import Product, ProductSize
from app.models.request import MeasureRequest
from app.models.shop import Shop


async def _seed(db_session):
    top = GarmentType(name="بالاتنه", is_active=True)
    db_session.add(top)
    await db_session.flush()
    account = Account(username="nakhonaghsh", password_hash=hash_password("p"), role="seller", is_active=True)
    db_session.add(account)
    await db_session.flush()
    shop = Shop(name="نخ و نقش", is_active=True, account_id=account.id)
    db_session.add(shop)
    await db_session.flush()
    product = Product(shop_id=shop.id, name="تی‌شرت", garment_type_id=top.id, numbers_kind="circumference", link_code="l1", is_active=True)
    db_session.add(product)
    await db_session.flush()
    size = ProductSize(product_id=product.id, name="مدیوم", sort_order=0)
    db_session.add(size)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(MeasureRequest(product_id=product.id, created_at=now, status="answered", recommended_size_id=size.id, photo_path=None, photo_delete_at=now, view_code="v1"))
    db_session.add(MeasureRequest(product_id=product.id, created_at=now, status="rejected", reject_reason="blurry", photo_path=None, photo_delete_at=now, view_code="v2"))
    await db_session.commit()
    return product


async def test_requests_list_scenario_15(client, db_session):
    await _seed(db_session)
    await client.post("/api/auth/login", json={"username": "nakhonaghsh", "password": "p"})
    r = await client.get("/api/requests")
    assert r.status_code == 200
    body = r.json()
    assert body["answered_count"] == 1
    assert body["rejected_count"] == 1
    assert len(body["requests"]) == 2

    serialised = str(body)
    # no photo path, no buyer-identifying field anywhere in the response
    assert "photo_path" not in serialised
    for forbidden in ["phone", "شماره", "instagram_handle", "buyer"]:
        assert forbidden not in serialised


async def test_no_endpoint_returns_a_photo_scenario_27(client, db_session):
    product = await _seed(db_session)
    await client.post("/api/auth/login", json={"username": "nakhonaghsh", "password": "p"})

    # every seller-facing read endpoint: none of them may carry a photo path
    r1 = await client.get("/api/requests")
    r2 = await client.get(f"/api/products/{product.id}/sizes")
    for r in (r1, r2):
        assert "photo_path" not in str(r.json())

    # and there is no route at all that serves the uploads directory
    from app.main import app

    paths = [route.path for route in app.routes]
    assert not any("photo" in p for p in paths)
    assert not any(p.startswith("/uploads") for p in paths)
