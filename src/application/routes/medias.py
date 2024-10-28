"""Реализация /medias."""

from fastapi import APIRouter

from .. import dependencies as dep
from .. import schemas
from ..models.crud import add_media

route = APIRouter(prefix="/medias", tags=["medias"])


@route.post("", response_model=schemas.MediaResult, name="Загрузить файл")
async def add_file(
    file: dep.file, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь загружает файл. Загрузка файла происходит через отправку формы."""
    media_id = await add_media(
        user_id=user.id, media=file, async_session=async_session
    )
    return {"media_id": media_id, "result": True}
