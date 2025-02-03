"""Реализация /tweets."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .. import dependencies as dep
from .. import schemas

route = APIRouter(prefix="/tweets", tags=["tweets"])


@route.get(
    "",
    response_model=schemas.Tweets,
    responses={400: {"model": schemas.TweetError}},
    name="Получить ленту",
)
async def get_tweets(
    user: dep.ApiKey, crud: dep.crud_controller, request: Request
):
    """Пользователь запрашивает ленту с твитами."""
    try:
        tweets = await crud.get_tweets_info(
            user_id=user.id,
            media_url=request.url_for("Загрузить файл"),
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
    tweet: schemas.TweetIn, user: dep.ApiKey, crud: dep.crud_controller
):
    """Пользователь создает новый твит."""
    result = await crud.add_tweet(
        user_id=user.id,
        tweet_data=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids,
    )
    return result


@route.delete("/{id}", response_model=schemas.Result, name="Удалить твит")
async def drop_tweet(id: int, user: dep.ApiKey, crud: dep.crud_controller):
    """Пользователь удаляет твит. Удалить можно только собственный твит."""
    result = await crud.remove_tweet(user_id=user.id, tweet_id=id)
    return {"result": result}


@route.post(
    "/{id}/likes", response_model=schemas.Result, name="Добавить 'Нравится'"
)
async def add_like(id: int, user: dep.ApiKey, crud: dep.crud_controller):
    """Пользователь ставит отметку 'Нравится' на твит."""
    result = await crud.create_like(user_id=user.id, tweet_id=id)
    return {"result": result}


@route.delete(
    "/{id}/likes", response_model=schemas.Result, name="Снять 'Нравится'"
)
async def drop_like(id: int, user: dep.ApiKey, crud: dep.crud_controller):
    """Пользователь снимает отметку 'Нравится' с твита."""
    result = await crud.remove_like(user_id=user.id, tweet_id=id)
    return {"result": result}
