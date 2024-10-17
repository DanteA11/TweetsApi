from fastapi import APIRouter

from .. import schemas

route = APIRouter(prefix="/users", tags=["users"])


@route.get("/me", response_model=schemas.Users, name="Мой профиль")
async def get_me():
    """Пользователь запрашивает информацию о своем профиле."""


@route.get("/{id}", response_model=schemas.Users, name="Профиль по ID")
async def get_user_by_id(id: int):
    """Пользователь запрашивает информацию о профиле другого пользователя по ID."""


@route.post("/{id}/follow", response_model=schemas.Result, name="Подписаться")
async def subscribe_to_user(id: int):
    """Пользователь подписывается на другого пользователя."""


@route.delete("/{id}/follow", response_model=schemas.Result, name="Отписаться")
async def unsubscribe_to_user(id: int):
    """Пользователь отписывается от другого пользователя."""
