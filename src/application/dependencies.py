"""
Зависимости приложения.

В модуле находятся классы и функции, которые FastApi
будет использовать в качестве зависимостей.
"""

from __future__ import annotations

from typing import Annotated, Any, Awaitable, Callable

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from .models import User, crud
from .models.database import get_async_engine
from .models.database import get_async_session as get_session
from .models.database import start_conn, stop_conn
from .settings import get_settings
from .utils import MetaSingleton


class AsyncEngineGetter(metaclass=MetaSingleton):
    """
    Класс-синглтон для получения объекта AsyncEngine.

    Принимает модель настроек, в случае,
    если не передано, инициализирует модель по умолчанию.
    Из модели забирается database_url и используется
    для инициализации AsyncEngine.

    Экземпляр класса - вызываемый, при вызове
    инициализирует и возвращает AsyncEngine.

    :param settings: Модель настроек. Должна иметь свойство database_url.
    """

    def __init__(self, settings: BaseModel | None = None):
        settings = settings or get_settings()
        self.__engine: AsyncEngine | None = None
        self.database_url = settings.database_url  # type: ignore

    def __call__(self) -> AsyncEngine:
        """Вызов экземпляра класса."""
        return self.engine

    @property
    def engine(self):
        """Асинхронный движок."""
        if not self.__engine:
            self.__engine = get_async_engine(self.database_url)
        return self.__engine


class Lifespan:
    """
    Класс для активации событий жизненного цикла.

    Принимает AsyncEngine, если не передано, то инициализирует
    объект класса AsyncEngineGetter и использует его для получения движка.

    Экземпляр класса можно использовать как контекстный менеджер,
    при вызове нужно передать экземпляр приложения FasApi.

    Для использования собственных функций для установки цикла событий
    необходимо установить их после инициализации экземпляра класса. Сделать
    это можно, через параметры: start_async_func, start_kwargs и
    stop_async_func, stop_kwargs. Они заменяют собой установки по умолчанию.

    :param drop_all: Опциональный параметр. Указывает нужно ли удалять
        таблицы в начале и в конце контекста. Используется только
        если установлены аргументы по умолчанию.
    """

    _async_funcs: dict[str, Callable[..., Awaitable]] = {
        "start": start_conn,
        "stop": stop_conn,
    }
    _kwargs_for_funcs: dict[str, dict[str, Any]] = {"start": {}, "stop": {}}

    def __init__(self, *, drop_all: bool = False):
        async_engine_getter = AsyncEngineGetter()
        engine = async_engine_getter()
        self.start_kwargs = self.stop_kwargs = {
            "engine": engine,
            "drop_all": drop_all,
        }

    def __call__(self, app: FastAPI) -> "Lifespan":
        """
        Вызов экземпляра класса.

        Можно вызвать, передав экземпляр приложения и
        использовать как контекстный менеджер.

        :param app: Экземпляр приложения FastApi

        :return: Экземпляр класса.
        """
        self.app = app
        return self

    async def __aenter__(self):
        """Вход в менеджер контекста."""
        start_coro = self._async_funcs["start"]
        kwargs = self._kwargs_for_funcs["start"]
        await start_coro(**kwargs)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из менеджера контекста."""
        stop_coro = self._async_funcs["stop"]
        kwargs = self._kwargs_for_funcs["stop"]
        await stop_coro(**kwargs)

    @property
    def start_async_func(self) -> Callable[..., Awaitable] | None:
        """Функция начала контекста."""
        return self._async_funcs.get("start")

    @start_async_func.setter
    def start_async_func(self, async_func: Callable[..., Awaitable]):
        """Функция начала контекста."""
        self._async_funcs["start"] = async_func

    @property
    def stop_async_func(self) -> Callable[..., Awaitable] | None:
        """Функция конца контекста."""
        return self._async_funcs.get("stop")

    @stop_async_func.setter
    def stop_async_func(self, async_func: Callable[..., Awaitable]):
        """Функция конца контекста."""
        self._async_funcs["stop"] = async_func

    @property
    def start_kwargs(self):
        """Аргументы функции начала контекста."""
        return self._kwargs_for_funcs["start"]

    @start_kwargs.setter
    def start_kwargs(self, kwargs):
        """Аргументы функции начала контекста."""
        self._kwargs_for_funcs["start"] = kwargs

    @property
    def stop_kwargs(self):
        """Аргументы функции конца контекста."""
        return self._kwargs_for_funcs["stop"]

    @stop_kwargs.setter
    def stop_kwargs(self, kwargs):
        """Аргументы функции конца контекста."""
        self._kwargs_for_funcs["stop"] = kwargs


def get_async_session(engine: async_engine):
    """
    Функция для получения конструктора асинхронной сессии.

    Используется в качестве зависимости в приложении.

    :param engine: Асинхронный движок.

    :return: Объект конструктора асинхронной сессии.
    """
    return get_session(engine)


async def get_user_by_api_key(
    api_key: Annotated[str, Header(description="Ключ для авторизации")],
    a_session: async_session,
):
    """
    Зависимость для проверки наличия пользователя в базе по api-key заголовку.

    :param api_key: Строка заголовка.
    :param a_session: Объект асинхронной сессии.

    :return: Пользователь
    :raise HTTPException: Выбрасывает, если пользователь не найден.
    """
    async with a_session() as session:
        user = await crud.get_user_by_api_key(
            api_key=api_key, async_session=session
        )
        if not user:
            raise HTTPException(
                status_code=400, detail="api-key header invalid"
            )
        return user


engine_getter = AsyncEngineGetter()
ApiKey = Annotated[User, Depends(get_user_by_api_key)]
async_engine = Annotated[AsyncEngine, Depends(engine_getter)]
async_session = Annotated[
    async_sessionmaker[AsyncSession], Depends(get_async_session)
]
