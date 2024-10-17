from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import schemas

route = APIRouter(prefix="/tweets", tags=["tweets"])


@route.get(
    "",
    response_model=schemas.Tweets,
    responses={400: {"model": schemas.TweetError}},
    name="Получить ленту",
)
async def get_tweets():
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
async def create_tweet(tweet: schemas.TweetIn):
    """Пользователь создает новый твит."""


@route.delete("/{id}", response_model=schemas.Result, name="Удалить твит")
async def drop_tweet(id: int):
    """Пользователь удаляет твит. Удалить можно только собственный твит."""


@route.post("/{id}/likes", response_model=schemas.Result, name="Добавить 'Нравится'")
async def add_like(id: int):
    """Пользователь ставит отметку 'Нравится' на твит."""


@route.delete("/{id}/likes", response_model=schemas.Result, name="Снять 'Нравится'")
async def drop_like(id: int):
    """Пользователь снимает отметку 'Нравится' с твита."""
