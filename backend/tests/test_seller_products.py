from app.core.security import hash_password
from app.models.account import Account
from app.models.garment import GarmentType, MeasurementCriterion
from app.models.shop import Shop


async def seed_garment_types(db_session):
    top = GarmentType(id=1, name="بالاتنه", is_active=True)
    db_session.add(top)
    await db_session.flush()
    criteria = [
        MeasurementCriterion(garment_type_id=top.id, name="دورِ سینه", is_main=True, kind="circumference", where_text="x", measure_rule="chest_width", sort_order=1),
        MeasurementCriterion(garment_type_id=top.id, name="طولِ لباس", is_main=True, kind="length", where_text="x", measure_rule="garment_length", sort_order=2),
        MeasurementCriterion(garment_type_id=top.id, name="عرضِ شانه", is_main=False, kind="length", where_text="x", measure_rule="shoulder_width", sort_order=3),
    ]
    db_session.add_all(criteria)
    await db_session.commit()
    return top, criteria


async def make_seller(db_session, username="nakhonaghsh"):
    account = Account(username=username, password_hash=hash_password("p"), role="seller", is_active=True)
    db_session.add(account)
    await db_session.flush()
    shop = Shop(name="نخ و نقش", is_active=True, account_id=account.id)
    db_session.add(shop)
    await db_session.commit()
    return shop, account


async def login_seller(client, db_session):
    shop, account = await make_seller(db_session)
    await client.post("/api/auth/login", json={"username": account.username, "password": "p"})
    return shop


async def test_create_product_scenario_11(client, db_session):
    top, _ = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    r = await client.post(
        "/api/products",
        json={"name": "تی‌شرت اورسایزِ کتان", "garment_type_id": top.id, "numbers_kind": "circumference"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["is_active"] is False
    assert body["link_code"]


async def test_incomplete_chart_does_not_activate_link_scenario_12(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()

    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "اسمال"})).json()
    s2 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "مدیوم"})).json()

    chest_id = criteria[0].id
    length_id = criteria[1].id
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": chest_id, "value_cm": 96})
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": length_id, "value_cm": 66})
    # s2 left incomplete (missing length)
    await client.put(f"/api/sizes/{s2['id']}/measurements", json={"criterion_id": chest_id, "value_cm": 104})

    link = (await client.get(f"/api/products/{p['id']}/link")).json()
    assert link["is_active"] is False
    assert link["complete_count"] == 1
    assert link["total_count"] == 2


async def test_completing_chart_activates_link_scenario_13(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "اسمال"})).json()
    chest_id, length_id = criteria[0].id, criteria[1].id
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": chest_id, "value_cm": 96})
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": length_id, "value_cm": 66})

    link = (await client.get(f"/api/products/{p['id']}/link")).json()
    assert link["is_active"] is True


async def test_zero_and_negative_rejected_scenario_13(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "اسمال"})).json()
    r = await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": criteria[0].id, "value_cm": 0})
    assert r.status_code == 400
    r2 = await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": criteria[0].id, "value_cm": -5})
    assert r2.status_code == 400


async def test_incomplete_size_added_to_live_link_does_not_take_it_down_scenario_19(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "مدیوم"})).json()
    chest_id, length_id = criteria[0].id, criteria[1].id
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": chest_id, "value_cm": 104})
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": length_id, "value_cm": 68})

    link = (await client.get(f"/api/products/{p['id']}/link")).json()
    assert link["is_active"] is True

    # add a new empty size — link must stay live
    await client.post(f"/api/products/{p['id']}/sizes", json={"name": "دو‌ایکس‌لارج"})
    link2 = (await client.get(f"/api/products/{p['id']}/link")).json()
    assert link2["is_active"] is True

    sizes = (await client.get(f"/api/products/{p['id']}/sizes")).json()
    incomplete = [s for s in sizes if not s["is_complete"]]
    assert len(incomplete) == 1
    assert incomplete[0]["name"] == "دو‌ایکس‌لارج"


async def test_numbers_kind_switch_locked_and_clears_scenario_20(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "اسمال"})).json()
    await client.put(f"/api/sizes/{s1['id']}/measurements", json={"criterion_id": criteria[0].id, "value_cm": 96})

    # without confirm -> refused
    r = await client.post(f"/api/products/{p['id']}/numbers-kind", json={"numbers_kind": "width", "confirm": False})
    assert r.status_code == 409

    sizes_before = (await client.get(f"/api/products/{p['id']}/sizes")).json()
    assert sizes_before[0]["measurements"]

    # with confirm -> switches and clears
    r2 = await client.post(f"/api/products/{p['id']}/numbers-kind", json={"numbers_kind": "width", "confirm": True})
    assert r2.status_code == 200
    assert r2.json()["numbers_kind"] == "width"

    sizes_after = (await client.get(f"/api/products/{p['id']}/sizes")).json()
    assert sizes_after[0]["measurements"] == {}


async def test_delete_size_scenario_21(client, db_session):
    top, criteria = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    s1 = (await client.post(f"/api/products/{p['id']}/sizes", json={"name": "دو‌ایکس‌لارج"})).json()
    r = await client.delete(f"/api/sizes/{s1['id']}")
    assert r.status_code == 200


async def test_deactivate_product_scenario_16(client, db_session):
    top, _ = await seed_garment_types(db_session)
    await login_seller(client, db_session)
    p = (await client.post(
        "/api/products", json={"name": "p", "garment_type_id": top.id, "numbers_kind": "circumference"}
    )).json()
    r = await client.post(f"/api/products/{p['id']}/deactivate")
    assert r.status_code == 200
    updated = (await client.get(f"/api/products/{p['id']}")).json()
    assert updated["is_active"] is False
