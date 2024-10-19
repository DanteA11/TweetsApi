import asyncio
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from application import create_app
from application.dependencies import AsyncEngineGetter, get_async_session
from application.models.database import start_conn, stop_conn


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app(engine) -> Generator[FastAPI, None, None]:
    asyncio.run(start_conn(engine, drop_all=True))
    app_: FastAPI = create_app(drop_all=False)
    yield app_
    asyncio.run(stop_conn(engine, drop_all=True))


@pytest.fixture(scope="module")
def client(app) -> TestClient:
    client_ = TestClient(app)
    return client_


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    engine_getter = AsyncEngineGetter()
    engine_: AsyncEngine = engine_getter()
    return engine_


@pytest.fixture
async def session(engine):
    async_session: async_sessionmaker[AsyncSession] = await get_async_session(
        engine
    )
    return async_session


@pytest.fixture(scope="module")
def api_url():
    return "/api{uri}"


@pytest.fixture(scope="module")
def users_url(api_url):
    return api_url.format(uri="/users")
