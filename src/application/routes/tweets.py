"""Реализация /tweets."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .. import dependencies as dep
from .. import schemas
from ..models.crud import (
    add_tweet,
    create_like,
    get_tweets_info,
    remove_like,
    remove_tweet,
)

route = APIRouter(prefix="/tweets", tags=["tweets"])


@route.get(
    "",
    response_model=schemas.Tweets,
    responses={400: {"model": schemas.TweetError}},
    name="Получить ленту",
)
async def get_tweets(
    user: dep.ApiKey, async_session: dep.async_session, request: Request
):
    """Пользователь запрашивает ленту с твитами."""
    try:
        tweets = await get_tweets_info(
            user_id=user.id,
            base_url=request.base_url,
            async_session=async_session,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={
                "result": False,
                "error_message": exc,
                "error_type": type(exc).__name__,
            },
        )
    return {"result": True, "tweets": tweets}


@route.post("", response_model=schemas.TweetResult, name="Создать твит")
async def create_tweet(
    tweet: schemas.TweetIn, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь создает новый твит."""
    result = await add_tweet(
        user_id=user.id,
        tweet_data=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids,
        async_session=async_session,
    )
    return result


@route.delete("/{id}", response_model=schemas.Result, name="Удалить твит")
async def drop_tweet(
    id: int, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь удаляет твит. Удалить можно только собственный твит."""
    result = await remove_tweet(
        user_id=user.id, tweet_id=id, async_session=async_session
    )
    return {"result": result}


@route.post(
    "/{id}/likes", response_model=schemas.Result, name="Добавить 'Нравится'"
)
async def add_like(
    id: int, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь ставит отметку 'Нравится' на твит."""
    result = await create_like(
        user_id=user.id, tweet_id=id, async_session=async_session
    )
    return {"result": result}


@route.delete(
    "/{id}/likes", response_model=schemas.Result, name="Снять 'Нравится'"
)
async def drop_like(
    id: int, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь снимает отметку 'Нравится' с твита."""
    result = await remove_like(
        user_id=user.id, tweet_id=id, async_session=async_session
    )
    return {"result": result}
