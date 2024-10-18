from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .models import crud
from .models.database import get_async_engine, start_conn, stop_conn
from .models.models import User
from .settings import Settings
from .utils import MetaSingleton


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


class AsyncEngineGetter(metaclass=MetaSingleton):
    def __init__(self, settings: BaseModel | None = None):
        settings = settings or get_settings()
        self.__engine = None
        self.database_url = settings.database_url

    def __call__(self) -> AsyncEngine:
        return self.engine

    @property
    def engine(self) -> AsyncEngine:
        if not self.__engine:
            self.__engine = get_async_engine(self.database_url)
        return self.__engine


class Lifespan:
    def __init__(self, *, engine: AsyncEngine | None = None, drop_all: bool = False):
        self.drop_all = drop_all
        if engine:
            self.engine = engine
            return
        async_engine_getter = AsyncEngineGetter()
        self.engine = async_engine_getter()

    def __call__(self, app: FastAPI):
        self.app = app
        return self

    async def __aenter__(self):
        await start_conn(engine=self.engine, drop_all=self.drop_all)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await stop_conn(engine=self.engine, drop_all=self.drop_all)


async def get_async_session(engine: async_engine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_user_by_api_key(
        api_key: Annotated[str, Header(description="Ключ для авторизации")],
        a_session: async_session,
):
    async with a_session() as session:
        user = await crud.get_user_by_api_key(api_key=api_key, async_session=session)
        if not user:
            raise HTTPException(status_code=400, detail="api-key header invalid")
        return user


ApiKey = Annotated[User, Depends(get_user_by_api_key)]
async_engine = Annotated[AsyncEngine, Depends(AsyncEngineGetter())]
async_session = Annotated[async_sessionmaker[AsyncSession], Depends(get_async_session)]
