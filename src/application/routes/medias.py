from fastapi import APIRouter, UploadFile

from .. import schemas

route = APIRouter(prefix="/medias", tags=["medias"])


@route.post("", response_model=schemas.MediaResult, name="Загрузить файл")
async def add_file(file: UploadFile):
    """Пользователь загружает файл. Загрузка файла происходит через отправку формы."""
