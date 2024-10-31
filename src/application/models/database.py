"""Функции для подключения к БД и базовый класс модели таблиц."""

from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для создания моделей таблиц."""

    def to_dict(self) -> dict[str, Any]:
        """Преобразование данных возвращенной модели в словарь."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore

    def __repr__(self) -> str:
        """Формирование отладочной информации."""
        res = ", ".join([f"{k}={v}" for k, v in self.to_dict().items()])
        return f"{type(self).__name__}({res})"


def get_async_engine(database_url: str) -> AsyncEngine:
    """
    Функция для получения асинхронного движка.

    :param database_url: Ссылка на БД.

    :return: Асинхронный движок.
    """
    engine = create_async_engine(database_url)
    return engine


def get_async_session(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Функция для получения конструктора асинхронной сессии.

    :param engine: Асинхронный движок.

    :return: Объект конструктора асинхронной сессии.
    """
    return async_sessionmaker(engine, expire_on_commit=False)


async def start_conn(engine: AsyncEngine, drop_all: bool = False) -> None:
    """
    Функция выполняет действия, необходимые при подключении к БД.

    :param engine: Асинхронный движок.
    :param drop_all: Опциональный параметр.
    Указывает нужно ли удалять таблицы.
    """
    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def stop_conn(engine: AsyncEngine, drop_all: bool = False) -> None:
    """
    Функция выполняет действия, необходимые при отключении от БД.

    :param engine: Асинхронный движок.
    :param drop_all: Опциональный параметр.
    Указывает нужно ли удалять таблицы.
    """
    if drop_all:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
