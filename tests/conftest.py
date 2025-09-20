import os

import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.core.database import Base


@pytest_asyncio.fixture(scope="function", autouse=True)
async def async_db_session():  # noqa: ANN201
    async_engine = create_async_engine("sqlite+aiosqlite:///demo.db", echo=True)

    TestingAsyncSessionLocal = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        class_=AsyncSession,
    )
    Base.metadata.create_all(bind=create_engine("sqlite:///demo.db", echo=True))
    connection = await async_engine.connect()
    trans = await connection.begin()
    async_session = TestingAsyncSessionLocal(bind=connection)

    yield async_session

    if trans.is_valid:
        await trans.rollback()
    await async_session.close()
    await connection.close()
    os.remove("demo.db")  # noqa: PTH107
