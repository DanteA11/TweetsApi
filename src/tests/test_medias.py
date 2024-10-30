import asyncio

import aiofiles
import aiofiles.os
import pytest

from .factories import UserFactory


@pytest.mark.anyio
@pytest.mark.parametrize("name", ("image1.jpg", "image2.png"))
async def test_add_media(async_client, medias_url, session, media_path, name):
    files = await aiofiles.os.listdir(media_path)
    start_len = len(files)
    _, file_type = name.split(".")
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    async with aiofiles.open(f"./tests/files/{name}", "rb") as file:
        image = await file.read()
    key = api_key_obj.key
    response = await async_client.post(
        medias_url,
        headers={
            "api-key": key,
        },
        files={"file": (name, image, f"image/{file_type}")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result.get("result") is True
    media_id = result.get("media_id")
    assert isinstance(media_id, int)
    file_path = f"static/medias/{media_id}.{file_type}"
    files, check_file = await asyncio.gather(
        aiofiles.os.listdir(media_path),
        aiofiles.os.path.isfile(file_path),
    )
    assert len(files) == start_len + 1
    assert check_file is True
    await aiofiles.os.remove(file_path)


@pytest.mark.anyio
@pytest.mark.parametrize("name", ("text.txt", "data.csv"))
async def test_add_media_bad_type(async_client, medias_url, session, media_path, name):
    files = await aiofiles.os.listdir(media_path)
    start_len = len(files)
    _, file_type = name.split(".")
    user = await UserFactory.create()
    async with aiofiles.open(f"./tests/files/{name}", "rb") as file:
        api_key_obj, image = await asyncio.gather(
            user.awaitable_attrs.api_key, file.read()
        )
    key = api_key_obj.key
    response = await async_client.post(
        medias_url,
        headers={
            "api-key": key,
        },
        files={"file": (name, image, "image/png")},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "file"],
                "msg": f"Extension '{file_type}' not in supported ('png', 'jpg')",
                "type": "type_error",
            }
        ]
    }

    files = await aiofiles.os.listdir(media_path)
    assert len(files) == start_len
