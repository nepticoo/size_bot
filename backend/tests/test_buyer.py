import io
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import Image

from app.models.garment import GarmentType, MeasurementCriterion
from app.models.job import Job
from app.models.product import Product, ProductSize, SizeMeasurement
from app.models.request import ExtractedMeasurement, MeasureRequest
from app.models.shop import Shop
from app.models.account import Account
from app.core.security import hash_password


def _blank_jpeg_bytes():
    arr = np.full((300, 400, 3), 235, dtype=np.uint8)
    arr[::6, :] += 15  # sharp-enough texture to defeat the blur check
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return buf.getvalue()


async def _seed_top_type(db_session):
    top = GarmentType(id=1, name="بالاتنه", is_active=True)
    db_session.add(top)
    await db_session.flush()
    chest = MeasurementCriterion(garment_type_id=top.id, name="دورِ سینه", is_main=True, kind="circumference", where_text="x", measure_rule="chest_width", sort_order=1)
    length = MeasurementCriterion(garment_type_id=top.id, name="طولِ لباس", is_main=True, kind="length", where_text="x", measure_rule="garment_length", sort_order=2)
    db_session.add_all([chest, length])
    await db_session.commit()
    return top, chest, length


async def _seed_shop_and_product(db_session, top, chest, length, active=True):
    account = Account(username="nakhonaghsh", password_hash=hash_password("p"), role="seller", is_active=True)
    db_session.add(account)
    await db_session.flush()
    shop = Shop(name="نخ و نقش", is_active=active, account_id=account.id)
    db_session.add(shop)
    await db_session.flush()
    product = Product(
        shop_id=shop.id, name="تی‌شرت", garment_type_id=top.id, numbers_kind="circumference",
        link_code="abc12345", is_active=active,
    )
    db_session.add(product)
    await db_session.flush()

    sizes = {}
    for name, chest_cm, len_cm in [("اسمال", 96, 66), ("مدیوم", 104, 68), ("لارج", 112, 70), ("ایکس‌لارج", 120, 72)]:
        size = ProductSize(product_id=product.id, name=name, sort_order=len(sizes))
        db_session.add(size)
        await db_session.flush()
        db_session.add(SizeMeasurement(product_size_id=size.id, criterion_id=chest.id, value_cm=chest_cm))
        db_session.add(SizeMeasurement(product_size_id=size.id, criterion_id=length.id, value_cm=len_cm))
        sizes[name] = size
    await db_session.commit()
    return shop, product, sizes


async def test_public_product_visible_when_active(client, db_session):
    top, chest, length = await _seed_top_type(db_session)
    shop, product, _ = await _seed_shop_and_product(db_session, top, chest, length)
    r = await client.get(f"/api/p/{product.link_code}")
    assert r.status_code == 200
    assert r.json()["shop_name"] == "نخ و نقش"


async def test_inactive_product_404s_scenario_8(client, db_session):
    top, chest, length = await _seed_top_type(db_session)
    shop, product, _ = await _seed_shop_and_product(db_session, top, chest, length, active=False)
    r = await client.get(f"/api/p/{product.link_code}")
    assert r.status_code == 404


async def test_tampered_link_code_404s_not_another_shop_scenario_9(client, db_session):
    top, chest, length = await _seed_top_type(db_session)
    await _seed_shop_and_product(db_session, top, chest, length)
    r = await client.get("/api/p/doesnotexist")
    assert r.status_code == 404


async def test_no_card_photo_rejected_via_real_pipeline_scenario_2(client, db_session):
    top, chest, length = await _seed_top_type(db_session)
    shop, product, _ = await _seed_shop_and_product(db_session, top, chest, length)
    photo = _blank_jpeg_bytes()
    r = await client.post(
        f"/api/p/{product.link_code}/measure",
        files={"photo": ("p.jpg", photo, "image/jpeg")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["reason"] == "card_not_found"


async def test_answered_flow_creates_request_and_schedules_deletion(client, db_session, monkeypatch):
    top, chest, length = await _seed_top_type(db_session)
    shop, product, sizes = await _seed_shop_and_product(db_session, top, chest, length)

    def fake_pipeline(photo_bytes, criteria):
        by_rule = {c.measure_rule: c.id for c in criteria}
        return {
            "status": "measured",
            "values": {by_rule["chest_width"]: 104.0, by_rule["garment_length"]: 68.0},
        }

    monkeypatch.setattr("app.api.buyer.run_pipeline_sync", fake_pipeline)

    photo = _blank_jpeg_bytes()
    r = await client.post(
        f"/api/p/{product.link_code}/measure",
        files={"photo": ("p.jpg", photo, "image/jpeg")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    view_code = body["view_code"]

    r2 = await client.get(f"/api/r/{view_code}")
    assert r2.status_code == 200
    answer = r2.json()
    assert answer["status"] == "answered"
    assert answer["recommended_size"]["name"] == "مدیوم"
    assert "104" not in r2.text and "68.0" not in r2.text

    # a deletion job was scheduled
    from sqlalchemy import select
    jobs = (await db_session.execute(select(Job))).scalars().all()
    assert any(j.kind == "delete_photo" for j in jobs)


async def test_expired_answer_returns_410_scenario_7(client, db_session):
    top, chest, length = await _seed_top_type(db_session)
    shop, product, sizes = await _seed_shop_and_product(db_session, top, chest, length)

    past = datetime.now(timezone.utc) - timedelta(minutes=31)
    request = MeasureRequest(
        product_id=product.id,
        created_at=past,
        status="answered",
        recommended_size_id=sizes["مدیوم"].id,
        photo_path=None,
        photo_delete_at=past + timedelta(minutes=30),
        view_code="expiredcode",
    )
    db_session.add(request)
    await db_session.commit()

    r = await client.get("/api/r/expiredcode")
    assert r.status_code == 410
