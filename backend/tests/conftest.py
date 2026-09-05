import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.jobs.runner as jobs_runner
from app.db import Base, get_session
from app.main import app


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    # the background job runner opens its own sessions outside any request,
    # so it needs the same test engine explicitly rather than via DI
    original_session_local = jobs_runner.SessionLocal
    jobs_runner.SessionLocal = session_maker

    async with session_maker() as session:
        yield session

    app.dependency_overrides.clear()
    jobs_runner.SessionLocal = original_session_local
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
