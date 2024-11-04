"""Модуль содержит конструктор приложения и все зависимости к нему."""

from fastapi import FastAPI

from .app_logger import logger
from .dependencies import Lifespan
from .routes import medias, tweets, users
from .settings import get_settings
from .utils import update_schema_name


def create_app(*, drop_all: bool = False) -> FastAPI:
    """
    Функция конструктор приложения.

    :param drop_all: Опциональный параметр. Указывает нужно ли удалять
    таблицы в начале и в конце контекста.

    :return: Приложение.
    """
    _settings = get_settings()
    lifespan = Lifespan(drop_all=drop_all)
    app: FastAPI = FastAPI(
        root_path="/api", lifespan=lifespan, title=_settings.api_name
    )

    app.include_router(tweets.route)
    app.include_router(medias.route)
    app.include_router(users.route)

    update_schema_name(app, medias.add_file, "Media")

    return app
