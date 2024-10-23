import pytest
from sqlalchemy import select

from application.models import ApiKey, Like, Media, Subscribe, Tweet, User
from application.models.crud import create_like, get_by_id

from .factories import MediaFactory, TweetFactory, UserFactory


@pytest.mark.anyio
async def test_add_tweet_without_api_key(async_client, tweets_url):
    tweet_data = {"tweet_data": "My first tweet", "tweet_media_ids": []}
    response = await async_client.post(f"{tweets_url}", json=tweet_data)
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
async def test_add_tweet_without_media(async_client, tweets_url, session):
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    tweet_data = {"tweet_data": "My first tweet", "tweet_media_ids": []}
    response = await async_client.post(
        f"{tweets_url}", json=tweet_data, headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    tweet_id = result.get("tweet_id")
    assert tweet_id is not None
    assert isinstance(tweet_id, int)

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is not None
    assert user.id == tweet_obj.author_id


@pytest.mark.anyio
async def test_add_tweet_with_media_without_add_media(
    async_client, tweets_url, session
):
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    tweet_data = {"tweet_data": "My first tweet", "tweet_media_ids": [1, 2]}
    response = await async_client.post(
        f"{tweets_url}", json=tweet_data, headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is False
    tweet_id = result.get("tweet_id")
    assert tweet_id == -1

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is None


@pytest.mark.anyio
async def test_add_tweet_with_media(async_client, tweets_url, session):
    media = await MediaFactory.create()
    assert media.tweet_id is None

    media_id = media.id
    user = await media.awaitable_attrs.user
    api_key_obj = await user.awaitable_attrs.api_key
    tweet_data = {
        "tweet_data": "My first tweet",
        "tweet_media_ids": [media_id],
    }
    response = await async_client.post(
        f"{tweets_url}", json=tweet_data, headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    tweet_id = result.get("tweet_id")
    assert tweet_id is not None
    assert isinstance(tweet_id, int)

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is not None
    assert user.id == tweet_obj.author_id

    media_new = await get_by_id(
        id_=media_id, model=Media, async_session=session
    )
    assert media_new.tweet_id == tweet_id


@pytest.mark.anyio
async def test_add_tweet_with_not_my_media(async_client, tweets_url, session):
    media = await MediaFactory.create()
    assert media.tweet_id is None

    media_id = media.id
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    tweet_data = {
        "tweet_data": "My first tweet",
        "tweet_media_ids": [media_id],
    }
    response = await async_client.post(
        f"{tweets_url}", json=tweet_data, headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is False
    tweet_id = result.get("tweet_id")
    assert tweet_id == -1

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is None


@pytest.mark.anyio
async def test_add_like(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    user_id = user.id
    tweet_id = tweet.id
    response = await async_client.post(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    like_obj = like_res.scalars().first()
    assert like_obj is not None


@pytest.mark.anyio
async def test_add_like_again(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    user_id = user.id
    tweet_id = tweet.id
    response = await async_client.post(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    like_obj = like_res.scalars().first()
    assert like_obj is not None

    response = await async_client.post(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    result_field = result.get("result")
    assert result_field is False

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    likes = like_res.scalars().all()
    assert len(likes) == 1


@pytest.mark.anyio
async def test_add_like_to_non_existent_tweet(
    async_client, tweets_url, session
):
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    user_id = user.id
    tweet_id = 1000
    response = await async_client.post(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is False

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    like_obj = like_res.scalars().first()
    assert like_obj is None


@pytest.mark.anyio
async def test_remove_like(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    user_id = user.id
    tweet_id = tweet.id

    result = await create_like(
        user_id=user_id, tweet_id=tweet_id, async_session=session
    )
    assert result is True

    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    like_obj = like_res.scalars().first()
    assert like_obj is None


@pytest.mark.anyio
async def test_remove_like_again(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    user_id = user.id
    tweet_id = tweet.id

    result = await create_like(
        user_id=user_id, tweet_id=tweet_id, async_session=session
    )
    assert result is True

    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )

    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    query = select(Like).filter(
        Like.user_id == user_id, Like.tweet_id == tweet_id
    )
    like_res = await session.execute(query)
    like_obj = like_res.scalars().first()
    assert like_obj is None

    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )

    result = response.json()
    result_field = result.get("result")
    assert result_field is False


@pytest.mark.anyio
async def test_remove_like_to_non_existent_tweet(
    async_client, tweets_url, session
):
    user = await UserFactory.create()
    api_key_obj = await user.awaitable_attrs.api_key
    tweet_id = 1000
    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}/likes", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200

    result = response.json()
    result_field = result.get("result")
    assert result_field is False

# TODO добавить тест для get запроса.