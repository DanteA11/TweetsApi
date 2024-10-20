from typing import Any

import pytest
from sqlalchemy import select

from application.models import ApiKey, Subscribe, User
from application.models.crud import get_by_id

from .factories import UserFactory


@pytest.mark.anyio
@pytest.mark.parametrize("path", ("me", 1))
async def test_get_users_without_api_key(async_client, users_url, path):
    response = await async_client.get(f"{users_url}/{path}")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": None,
                "loc": ["header", "api-key"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }


@pytest.mark.anyio
async def test_get_users_me(async_client, users_url, session):
    user = await UserFactory.create()
    api_key_obj = await get_by_id(user.key_id, ApiKey, session)
    response = await async_client.get(
        f"{users_url}/me", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    await check_users_response_with_user_obj(user, result)


@pytest.mark.anyio
async def test_get_users_by_id(async_client, users_url, session):
    user = await UserFactory.create()
    api_key_obj = await get_by_id(user.key_id, ApiKey, session)
    user_id = user.id
    response = await async_client.get(
        f"{users_url}/{user_id}", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    await check_users_response_with_user_obj(user, result)


@pytest.mark.anyio
async def test_me_get_other(async_client, users_url, session):
    me = await UserFactory.create()
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id
    response = await async_client.get(
        f"{users_url}/{me_id - 1}", headers={"api-key": key}
    )
    assert response.status_code == 200
    result = response.json()

    await check_users_response(result)


@pytest.mark.anyio
async def test_subscribeto_yourself(async_client, users_url, session):
    me = await get_by_id(1, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    response = await async_client.post(
        f"{users_url}/{me.id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me.id, Subscribe.author_id == me.id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert subscribes == []


@pytest.mark.anyio
async def test_subscribe_to_other(async_client, users_url, session):
    me = await get_by_id(1, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id
    author_id = me_id + 1
    response = await async_client.post(
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me_id, Subscribe.author_id == author_id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert len(subscribes) == 1


@pytest.mark.anyio
async def test_subscribe_to_other_again(async_client, users_url, session):
    me = await get_by_id(2, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id
    author_id = me_id + 1
    response = await async_client.post(
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me_id, Subscribe.author_id == author_id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert len(subscribes) == 1
    subscribe = subscribes[0]
    assert subscribe.follower_id == me_id
    assert subscribe.author_id == author_id

    response = await async_client.post(
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me_id, Subscribe.author_id == author_id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert len(subscribes) == 1


@pytest.mark.anyio
async def test_subscribe_to_non_existent_user(
    async_client, users_url, session
):
    me = await get_by_id(1, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    author_id = 10000
    response = await async_client.post(
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me.id, Subscribe.author_id == me.id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert subscribes == []


@pytest.mark.anyio
async def test_unsubscribe_from_yourself(async_client, users_url, session):
    me = await get_by_id(1, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    response = await async_client.delete(
        f"{users_url}/{me.id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}


@pytest.mark.anyio
async def test_unsubscribe_from_other(async_client, users_url, session):
    me = await get_by_id(1, User, session)
    author = await UserFactory.create()
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id
    author_id = author.id
    response = await async_client.post(  # Создаем подписку
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me_id, Subscribe.author_id == author_id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert len(subscribes) == 1

    response = await async_client.delete(  # Удаляем подписку
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(
        Subscribe.follower_id == me_id, Subscribe.author_id == author_id
    )
    result = await session.execute(query)
    subscribes = result.scalars().all()
    assert len(subscribes) == 0


@pytest.mark.anyio
async def test_followers_field_users_me(async_client, users_url, session):
    me = await get_by_id(2, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id

    query = select(Subscribe).filter(Subscribe.author_id == me_id)
    result = await session.execute(query)
    followers = result.scalars().all()
    assert len(followers) > 0

    response = await async_client.get(
        f"{users_url}/me", headers={"api-key": key}
    )
    assert response.status_code == 200

    result = response.json()
    user_field = await check_users_response(result)
    followers_field = user_field["followers"]
    assert len(followers_field) == len(followers)
    follower_data = followers_field[0]
    follower_obj = followers[0]

    assert follower_data["id"] == follower_obj.follower_id


@pytest.mark.anyio
async def test_following_field_users_me(async_client, users_url, session):
    me = await get_by_id(2, User, session)
    api_key_obj = await get_by_id(me.key_id, ApiKey, session)
    key = api_key_obj.key
    me_id = me.id

    query = select(Subscribe).filter(Subscribe.follower_id == me_id)
    result = await session.execute(query)
    authors = result.scalars().all()
    assert len(authors) > 0

    response = await async_client.get(
        f"{users_url}/me", headers={"api-key": key}
    )
    assert response.status_code == 200

    result = response.json()
    user_field = await check_users_response(result)
    following_field = user_field["following"]
    assert len(following_field) == len(authors)
    following_data = following_field[0]
    author_obj = authors[0]

    assert following_data["id"] == author_obj.author_id


async def check_users_response_with_user_obj(
    user, response_data: dict[str, Any]
):
    user_field = await check_users_response(response_data)
    name_field = user_field["name"]
    id_field = user_field["id"]
    assert name_field == user.name
    assert id_field == user.id

    return user_field


async def check_users_response(response_data: dict[str, Any]):
    result = response_data
    assert result is not None
    assert isinstance(result, dict)

    result_field = result.get("result")
    assert result_field is not None
    assert isinstance(result_field, bool)

    user_field = result.get("user")
    assert user_field is not None
    assert isinstance(user_field, dict)

    followers_field = user_field.get("followers")
    assert followers_field is not None
    assert isinstance(followers_field, list)

    following_field = user_field.get("following")
    assert following_field is not None
    assert isinstance(following_field, list)

    name_field = user_field.get("name")
    assert name_field is not None
    assert isinstance(name_field, str)

    id_field = user_field.get("id")
    assert id_field is not None
    assert isinstance(id_field, int)

    return user_field
