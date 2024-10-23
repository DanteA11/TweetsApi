import asyncio
from typing import Generator

import aiofiles
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from application import create_app
from application.dependencies import AsyncEngineGetter, get_async_session_maker
from application.models.database import start_conn, stop_conn


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app(engine) -> Generator[FastAPI, None, None]:
    asyncio.run(start_conn(engine, drop_all=True))
    app_: FastAPI = create_app()
    yield app_
    asyncio.run(stop_conn(engine, drop_all=True))


@pytest.fixture(scope="module")
async def async_client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    engine_getter = AsyncEngineGetter()
    engine_: AsyncEngine = engine_getter()
    return engine_


@pytest.fixture
def session_maker(engine) -> async_sessionmaker[AsyncSession]:
    async_session_maker = get_async_session_maker(engine)
    return async_session_maker


@pytest.fixture
async def session(session_maker):
    async with session_maker() as session:
        yield session


@pytest.fixture(scope="module")
def api_url():
    return "/api{uri}"


@pytest.fixture(scope="module")
def users_url(api_url):
    return api_url.format(uri="/users")


@pytest.fixture(scope="module")
def medias_url(api_url):
    return api_url.format(uri="/medias")


@pytest.fixture(scope="module")
def tweets_url(api_url):
    return api_url.format(uri="/tweets")
