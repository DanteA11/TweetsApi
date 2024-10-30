import asyncio
from typing import Any

import pytest
from sqlalchemy import select

from application.models import ApiKey, Subscribe, User

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
    api_key_obj = await user.awaitable_attrs.api_key
    response = await async_client.get(
        f"{users_url}/me", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    await check_users_response_with_user_obj(user, result)


@pytest.mark.anyio
async def test_get_users_by_id(async_client, users_url, session):
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
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
    api_key_obj = await me.awaitable_attrs.api_key
    key = api_key_obj.key
    me_id = me.id
    response = await async_client.get(
        f"{users_url}/{me_id - 1}", headers={"api-key": key}
    )
    assert response.status_code == 200
    result = response.json()

    await check_users_response(result)


@pytest.mark.anyio
async def test_subscribe_to_yourself(async_client, users_url, session):
    me = await UserFactory.create()
    api_key_obj = await me.awaitable_attrs.api_key
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
    await subscribe_to_other(async_client, users_url, session)


@pytest.mark.anyio
async def test_subscribe_to_other_again(async_client, users_url, session):
    author_id, key, me_id = await subscribe_to_other(
        async_client, users_url, session
    )

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
    me = await UserFactory.create()
    api_key_obj = await me.awaitable_attrs.api_key
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
    me = await UserFactory.create()
    api_key_obj = await me.awaitable_attrs.api_key
    key = api_key_obj.key
    response = await async_client.delete(
        f"{users_url}/{me.id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}


@pytest.mark.anyio
async def test_unsubscribe_from_other(async_client, users_url, session):
    author_id, key, me_id = await subscribe_to_other(
        async_client, users_url, session
    )
    await unsubscribe_from_other(
        async_client, users_url, session, author_id, key, me_id
    )


@pytest.mark.anyio
async def test_unsubscribe_from_other_again(async_client, users_url, session):
    author_id, key, me_id = await subscribe_to_other(
        async_client, users_url, session
    )
    await unsubscribe_from_other(
        async_client, users_url, session, author_id, key, me_id
    )
    response = await async_client.delete(  # Удаляем подписку
        f"{users_url}/{author_id}/follow", headers={"api-key": key}
    )
    assert response.status_code == 200
    assert response.json() == {"result": False}


@pytest.mark.anyio
async def test_followers_field_users_me(async_client, users_url, session):
    me = await UserFactory.create()
    user = await UserFactory.create()
    me_id = me.id
    user_api_key_obj, me_api_key_obj = await asyncio.gather(
        user.awaitable_attrs.api_key, me.awaitable_attrs.api_key
    )
    user_key = user_api_key_obj.key
    me_key = me_api_key_obj.key

    response = await async_client.post(
        f"{users_url}/{me_id}/follow", headers={"api-key": user_key}
    )

    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(Subscribe.author_id == me_id)
    result, response = await asyncio.gather(
        session.execute(query),
        async_client.get(f"{users_url}/me", headers={"api-key": me_key}),
    )
    followers = result.scalars().all()
    assert len(followers) > 0
    assert response.status_code == 200

    result = response.json()
    user_field = await check_users_response(result)
    followers_field = user_field["followers"]
    assert len(followers_field) == len(followers)

    for follower_data, follower_obj in zip(followers_field, followers):
        assert follower_data["id"] == follower_obj.follower_id


@pytest.mark.anyio
async def test_following_field_users_me(async_client, users_url, session):
    me = await UserFactory.create()
    user = await UserFactory.create()
    user_id = user.id
    me_id = me.id
    api_key_obj = await me.awaitable_attrs.api_key
    me_key = api_key_obj.key

    response = await async_client.post(
        f"{users_url}/{user_id}/follow", headers={"api-key": me_key}
    )

    assert response.status_code == 200
    assert response.json() == {"result": True}

    query = select(Subscribe).filter(Subscribe.follower_id == me_id)
    result, response = await asyncio.gather(
        session.execute(query),
        async_client.get(f"{users_url}/me", headers={"api-key": me_key}),
    )
    following = result.scalars().all()
    assert len(following) > 0
    assert response.status_code == 200

    result = response.json()
    user_field = await check_users_response(result)
    following_field = user_field["following"]
    assert len(following_field) == len(following)

    for following_data, following_obj in zip(following_field, following):
        assert following_data["id"] == following_obj.author_id


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


async def subscribe_to_other(async_client, users_url, session):
    me = await UserFactory.create()
    author = await UserFactory.create()
    api_key_obj = await me.awaitable_attrs.api_key
    key = api_key_obj.key
    me_id = me.id
    author_id = author.id
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

    return author_id, key, me_id


async def unsubscribe_from_other(
    async_client, users_url, session, author_id, key, me_id
):
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
