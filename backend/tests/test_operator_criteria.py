from app.core.security import hash_password
from app.models.account import Account
from app.models.garment import GarmentType, MeasurementCriterion


async def seed_garment_types(db_session):
    top = GarmentType(id=1, name="بالاتنه", is_active=True)
    bottom = GarmentType(id=2, name="پایین‌تنه", is_active=True)
    db_session.add_all([top, bottom])
    await db_session.commit()
    return top, bottom


async def make_operator(db_session):
    account = Account(username="admin", password_hash=hash_password("adminpass"), role="operator", is_active=True)
    db_session.add(account)
    await db_session.commit()


async def test_twelve_seed_criteria_present(client, db_session):
    top, bottom = await seed_garment_types(db_session)
    criteria = [
        MeasurementCriterion(garment_type_id=top.id, name="دورِ سینه", is_main=True, kind="circumference", where_text="x", measure_rule="chest_width", sort_order=1),
        MeasurementCriterion(garment_type_id=top.id, name="طولِ لباس", is_main=True, kind="length", where_text="x", measure_rule="garment_length", sort_order=2),
    ]
    db_session.add_all(criteria)
    await db_session.commit()
    await make_operator(db_session)
    await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})
    r = await client.get("/api/admin/criteria")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_add_criterion_and_reject_duplicate(client, db_session):
    top, _ = await seed_garment_types(db_session)
    await make_operator(db_session)
    await client.post("/api/auth/login", json={"username": "admin", "password": "adminpass"})

    r = await client.post(
        "/api/admin/criteria",
        json={
            "garment_type_id": top.id,
            "name": "دورِ یقه",
            "is_main": False,
            "kind": "circumference",
            "where_text": "دورِ یقه",
            "measure_rule": None,
        },
    )
    assert r.status_code == 200
    assert r.json()["name"] == "دورِ یقه"

    r2 = await client.post(
        "/api/admin/criteria",
        json={
            "garment_type_id": top.id,
            "name": "دورِ یقه",
            "is_main": False,
            "kind": "circumference",
            "where_text": "دورِ یقه",
        },
    )
    assert r2.status_code == 409
