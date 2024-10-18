import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from application import create_app
from application.dependencies import AsyncEngineGetter, get_async_session
from application.models.database import start_conn, stop_conn


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app(engine) -> FastAPI:
    asyncio.run(start_conn(engine, drop_all=True))
    app_ = create_app(drop_all=False)
    yield app_
    asyncio.run(stop_conn(engine, drop_all=True))


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    client_ = TestClient(app)
    return client_


@pytest.fixture(scope="module")
def engine() -> AsyncEngine:
    engine_getter = AsyncEngineGetter()
    engine_: AsyncEngine = engine_getter()
    return engine_


@pytest.fixture
async def session(engine):
    async_session: async_sessionmaker[AsyncSession] = await get_async_session(engine)
    return async_session
