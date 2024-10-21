"""Реализация /tweets."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import dependencies as dep
from .. import schemas
from ..models.crud import add_tweet

route = APIRouter(prefix="/tweets", tags=["tweets"])


@route.get(
    "",
    response_model=schemas.Tweets,
    responses={400: {"model": schemas.TweetError}},
    name="Получить ленту",
)
async def get_tweets(user: dep.ApiKey):
    """Пользователь запрашивает ленту с твитами."""
    try:
        ...
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={
                "result": False,
                "error_message": exc,
                "error_type": type(exc).__name__,
            },
        )


@route.post("", response_model=schemas.TweetResult, name="Создать твит")
async def create_tweet(
    tweet: schemas.TweetIn, user: dep.ApiKey, async_session: dep.async_session
):
    """Пользователь создает новый твит."""
    tweet_id = await add_tweet(
        user_id=user.id,
        tweet_data=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids,
        async_session=async_session,
    )
    return {"result": True, "tweet_id": tweet_id}


@route.delete("/{id}", response_model=schemas.Result, name="Удалить твит")
async def drop_tweet(id: int, user: dep.ApiKey):
    """Пользователь удаляет твит. Удалить можно только собственный твит."""


@route.post(
    "/{id}/likes", response_model=schemas.Result, name="Добавить 'Нравится'"
)
async def add_like(id: int, user: dep.ApiKey):
    """Пользователь ставит отметку 'Нравится' на твит."""


@route.delete(
    "/{id}/likes", response_model=schemas.Result, name="Снять 'Нравится'"
)
async def drop_like(id: int, user: dep.ApiKey):
    """Пользователь снимает отметку 'Нравится' с твита."""
