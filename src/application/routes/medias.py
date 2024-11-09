"""Реализация /medias."""

from fastapi import APIRouter

from .. import dependencies as dep
from .. import schemas

route = APIRouter(prefix="/medias", tags=["medias"])


@route.post("", response_model=schemas.MediaResult, name="Загрузить файл")
async def add_file(
    user: dep.ApiKey, file: dep.file, crud: dep.crud_controller
):
    """Пользователь загружает файл. Загрузка файла происходит через отправку формы."""
    media_id = await crud.add_media(user_id=user.id, media=file)
    return {"media_id": media_id, "result": True}
