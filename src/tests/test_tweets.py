import asyncio

import pytest
from sqlalchemy import select, update

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
async def test_remove_tweet(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    me = await tweet.awaitable_attrs.author
    api_key_obj = await me.awaitable_attrs.api_key
    tweet_id = tweet.id
    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    result_field = result.get("result")
    assert result_field is True

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is None


@pytest.mark.anyio
async def test_remove_not_my_tweet(async_client, tweets_url, session):
    tweet = await TweetFactory.create()
    me = await UserFactory.create()
    api_key_obj = await me.awaitable_attrs.api_key
    tweet_id = tweet.id
    response = await async_client.delete(
        f"{tweets_url}/{tweet_id}", headers={"api-key": api_key_obj.key}
    )
    assert response.status_code == 200
    result = response.json()
    result_field = result.get("result")
    assert result_field is False

    tweet_obj = await get_by_id(
        id_=tweet_id, model=Tweet, async_session=session
    )
    assert tweet_obj is not None
    assert tweet_id == tweet_obj.id


@pytest.mark.anyio
async def test_add_like(async_client, tweets_url, session):
    await add_like(async_client, tweets_url, session)


@pytest.mark.anyio
async def test_add_like_again(async_client, tweets_url, session):
    tweet_id, user_id, api_key_obj = await add_like(
        async_client, tweets_url, session
    )

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
    tweet_id, user_id, api_key_obj = await add_like(
        async_client, tweets_url, session
    )
    await remove_like(
        async_client, tweets_url, session, tweet_id, user_id, api_key_obj
    )


@pytest.mark.anyio
async def test_remove_like_again(async_client, tweets_url, session):
    tweet_id, user_id, api_key_obj = await add_like(
        async_client, tweets_url, session
    )
    await remove_like(
        async_client, tweets_url, session, tweet_id, user_id, api_key_obj
    )

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


@pytest.mark.anyio
async def test_get_tweets(
    async_client, tweets_url, session, base_url, medias_url
):
    me = await UserFactory.create()
    other = await UserFactory.create()
    tweet = await TweetFactory.create()
    media = await MediaFactory.create()

    author, me_key_obj = await asyncio.gather(
        tweet.awaitable_attrs.author, me.awaitable_attrs.api_key
    )
    me_key = me_key_obj.key
    me_id = me.id
    author_id = author.id
    tweet_id = tweet.id
    media_id = media.id
    other_id = other.id

    me_like = Like(user_id=me_id, tweet_id=tweet_id)
    other_like = Like(user_id=other_id, tweet_id=tweet_id)

    likes = (
        {"name": me.name, "user_id": me_id},
        {"name": other.name, "user_id": other_id},
    )
    subscribe = Subscribe(follower_id=me_id, author_id=author_id)
    session.add_all((subscribe, me_like, other_like))
    res = await session.execute(
        update(Media).filter(Media.id == media_id).values(tweet_id=tweet_id)
    )
    await session.commit()
    assert res.rowcount == 1

    response = await async_client.get(tweets_url, headers={"api-key": me_key})
    assert response.status_code == 200
    result = response.json()

    result_field = result.get("result")
    assert result_field is True
    tweets_field = result.get("tweets")
    assert isinstance(tweets_field, list)

    for tweet_field in tweets_field:
        id_field = tweet_field.get("id")
        assert id_field == tweet_id
        content_field = tweet_field.get("content")
        assert content_field == tweet.content
        attachments_filed = tweet_field.get("attachments")
        assert isinstance(attachments_filed, list)
        for attachment in attachments_filed:
            assert (
                attachment
                == f"{base_url}{medias_url}/{media_id}.{media.file_type}"
            )
        author_field = tweet_field.get("author")
        assert author_field == {"name": author.name, "id": author_id}
        likes_field = tweet_field.get("likes")
        assert isinstance(likes_field, list)
        for like in likes_field:
            assert like in likes


async def add_like(async_client, tweets_url, session):
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
    return tweet_id, user_id, api_key_obj


async def remove_like(
    async_client, tweets_url, session, tweet_id, user_id, api_key_obj
):
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
