from datetime import datetime, timedelta, timezone

from app.core.storage import LocalStorage
from app.jobs.runner import run_due_jobs, sweep_overdue_photos
from app.models.job import Job
from app.models.product import Product
from app.models.request import MeasureRequest


async def _make_product(db_session):
    from app.models.account import Account
    from app.models.garment import GarmentType
    from app.models.shop import Shop
    from app.core.security import hash_password

    top = GarmentType(name="بالاتنه", is_active=True)
    db_session.add(top)
    await db_session.flush()
    account = Account(username="s", password_hash=hash_password("p"), role="seller", is_active=True)
    db_session.add(account)
    await db_session.flush()
    shop = Shop(name="shop", is_active=True, account_id=account.id)
    db_session.add(shop)
    await db_session.flush()
    product = Product(
        shop_id=shop.id, name="p", garment_type_id=top.id, numbers_kind="circumference",
        link_code="link1", is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    return product


async def test_due_job_runs_and_deletes_photo(db_session, tmp_path, monkeypatch):
    storage = LocalStorage(base_dir=tmp_path)
    monkeypatch.setattr("app.jobs.handlers._storage", storage)

    product = await _make_product(db_session)
    key = storage.save(b"fake photo bytes", ".jpg")

    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    request = MeasureRequest(
        product_id=product.id, created_at=past, status="answered",
        photo_path=key, photo_delete_at=past, view_code="v1",
    )
    db_session.add(request)
    await db_session.flush()
    db_session.add(Job(kind="delete_photo", run_at=past, payload={"request_id": request.id}))
    await db_session.commit()

    await run_due_jobs()

    await db_session.refresh(request)
    assert request.photo_path is None
    assert not (tmp_path / key).exists()


async def test_startup_sweep_catches_overdue_photo_missed_by_jobs(db_session, tmp_path, monkeypatch):
    storage = LocalStorage(base_dir=tmp_path)
    monkeypatch.setattr("app.jobs.runner.LocalStorage", lambda: storage)

    product = await _make_product(db_session)
    key = storage.save(b"fake photo bytes", ".jpg")

    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    request = MeasureRequest(
        product_id=product.id, created_at=past, status="answered",
        photo_path=key, photo_delete_at=past, view_code="v2",
    )
    db_session.add(request)
    await db_session.commit()
    # deliberately no Job row — simulating one lost while the process was down

    await sweep_overdue_photos()

    await db_session.refresh(request)
    assert request.photo_path is None
    assert not (tmp_path / key).exists()
