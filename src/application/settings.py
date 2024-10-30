"""Настройки приложения."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.

    Класс получает данные из окружения.

    :arg database_url: Ссылка на базу данных.
    """

    database_url: str
    max_image_size: int
    media_path: str
    media_extensions: tuple[str, ...] = ("png", "jpg")

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """Функция возвращает настройки."""
    return Settings()  # type: ignore
