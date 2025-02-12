"""
Зависимости приложения.

В модуле находятся классы и функции, которые FastApi
будет использовать в качестве зависимостей.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, AsyncGenerator, Awaitable, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from .models import CrudController, User
from .models.database import get_async_engine
from .models.database import get_async_session as get_session
from .models.database import start_conn, stop_conn
from .settings import get_settings
from .utils import MetaSingleton

SETTINGS = get_settings()
logger_name = f"{SETTINGS.api_name}.{__name__}"
logger = logging.getLogger(logger_name)
logger.setLevel(SETTINGS.log_level)
DEBUG = logger.isEnabledFor(
    logging.DEBUG  # https://docs.python.org/3/howto/logging.html#optimization
)


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

    def __init__(self, settings: BaseModel | None = None) -> None:
        settings = settings or SETTINGS
        self.__engine: AsyncEngine | None = None
        self.database_url = settings.database_url  # type: ignore

    def __call__(self) -> AsyncEngine:
        """Вызов экземпляра класса."""
        return self.engine

    @property
    def engine(self) -> AsyncEngine:
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

    def __init__(self, *, drop_all: bool = False) -> None:
        async_engine_getter = AsyncEngineGetter()
        engine = async_engine_getter.engine
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

    async def __aenter__(self) -> None:
        """Вход в менеджер контекста."""
        start_coro = self._async_funcs["start"]
        kwargs = self._kwargs_for_funcs["start"]
        await start_coro(**kwargs)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
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
    def start_kwargs(self) -> dict[str, Any]:
        """Аргументы функции начала контекста."""
        return self._kwargs_for_funcs["start"]

    @start_kwargs.setter
    def start_kwargs(self, kwargs) -> None:
        """Аргументы функции начала контекста."""
        self._kwargs_for_funcs["start"] = kwargs

    @property
    def stop_kwargs(self) -> dict[str, Any]:
        """Аргументы функции конца контекста."""
        return self._kwargs_for_funcs["stop"]

    @stop_kwargs.setter
    def stop_kwargs(self, kwargs) -> None:
        """Аргументы функции конца контекста."""
        self._kwargs_for_funcs["stop"] = kwargs


def get_async_session_maker(
    engine: Annotated[AsyncEngine, Depends(AsyncEngineGetter())]
) -> async_sessionmaker[AsyncSession]:
    """
    Функция для получения конструктора асинхронной сессии.

    Используется в качестве зависимости в приложении.

    :param engine: Асинхронный движок.

    :return: Конструктор асинхронной сессии.
    """
    return get_session(engine)


async def get_crud_controller(
    session_maker: Annotated[
        async_sessionmaker[AsyncSession], Depends(get_async_session_maker)
    ]
) -> AsyncGenerator[CrudController, None]:
    """
    Функция-генератор для контроллера для управления базой данных.

    :param session_maker: Асинхронный движок.

    :return: Контроллер
    """
    async with session_maker() as session:
        yield CrudController(session=session)


async def get_user_by_api_key(
    api_key: Annotated[str, Header(description="Ключ для авторизации")],
    crud: crud_controller,
) -> User:
    """
    Зависимость для проверки наличия пользователя в базе по api-key заголовку.

    :param api_key: Строка заголовка.
    :param crud: Контроллер для управления запросами к базе данных.

    :return: Пользователь
    :raise HTTPException: Выбрасывает, если пользователь не найден.
    """
    user = await crud.get_user_by_api_key(api_key=api_key)
    if not user:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["header", "api-key"],
                    "input": api_key,
                    "msg": "api-key header invalid",
                    "type": "assertion_error",
                }
            ],
        )
    return user


def check_file(file: UploadFile) -> UploadFile:
    """
    Функция проверяет файл на соответствие типа и размера.

    :param file: Файл.
    :return: Файл.
    :raise HTTPException: Выбрасывает, если файл не прошел валидацию.
    """
    if DEBUG:
        logger.debug("file=%s", file)
    details = []
    detail: dict[str, list | str] = {
        "loc": ["body", "file"],
    }
    file_size = file.size
    max_size = SETTINGS.max_image_size
    if not file_size or file_size > max_size:
        if DEBUG:
            logger.debug(
                "Не найден размер файла или размер "
                "файла больше максимально допустимого"
            )
        res = detail.copy()
        res["msg"] = (
            f"File size ({file.size}) is "
            f"larger than the maximum file size ({max_size})"
        )
        res["type"] = "value_error"
        details.append(res)

    supported_extensions = SETTINGS.media_extensions
    filename = file.filename or ""
    *others, extension = filename.split(".")
    if not others:
        extension = ""
    if not extension or extension.lower() not in supported_extensions:
        if DEBUG:
            logger.debug(
                "У файла не указано расширение или расширение недопустимо"
            )
        res = detail.copy()
        res["msg"] = (
            f"Extension '{extension}' "
            f"not in supported {supported_extensions}"
        )
        res["type"] = "type_error"
        details.append(res)

    if details:
        logger.info("Функция выбросила исключение")
        raise HTTPException(status_code=422, detail=details)
    logger.info("Функция вернула файл")
    return file


crud_controller = Annotated[CrudController, Depends(get_crud_controller)]
ApiKey = Annotated[User, Depends(get_user_by_api_key)]
file = Annotated[UploadFile, Depends(check_file)]
