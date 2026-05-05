from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.base import Base
from app.models.tenancy import Tenant, User

TEST_DB_URL = settings.database_url


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)


@pytest.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def tenant_a(db: AsyncSession) -> Tenant:
    t = Tenant(name="Tenant A")
    db.add(t)
    await db.flush()
    return t


@pytest.fixture
async def tenant_b(db: AsyncSession) -> Tenant:
    t = Tenant(name="Tenant B")
    db.add(t)
    await db.flush()
    return t


@pytest.fixture
async def user_a(db: AsyncSession, tenant_a: Tenant) -> User:
    u = User(
        tenant_id=tenant_a.id,
        clerk_user_id=f"clerk_{uuid.uuid4().hex}",
        email="a@example.com",
    )
    db.add(u)
    await db.flush()
    return u


@pytest.fixture
async def user_b(db: AsyncSession, tenant_b: Tenant) -> User:
    u = User(
        tenant_id=tenant_b.id,
        clerk_user_id=f"clerk_{uuid.uuid4().hex}",
        email="b@example.com",
    )
    db.add(u)
    await db.flush()
    return u
