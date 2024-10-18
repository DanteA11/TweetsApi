from fastapi import APIRouter

from .. import dependencies as dep
from .. import schemas
from ..models.crud import get_full_user_info

route = APIRouter(prefix="/users", tags=["users"])


@route.get("/me", response_model=schemas.Users, name="Мой профиль")
async def get_me(user: dep.ApiKey, async_session: dep.async_session):
    """Пользователь запрашивает информацию о своем профиле."""
    async with async_session() as session:
        result = await get_full_user_info(user.id, session, user=user)
        return {"result": True, "user": result}


@route.get("/{id}", response_model=schemas.Users, name="Профиль по ID")
async def get_user_by_id(id: int, user: dep.ApiKey, async_session: dep.async_session):
    """Пользователь запрашивает информацию о профиле другого пользователя по ID."""
    async with async_session() as session:
        user_data = await get_full_user_info(id, session)
        result = {"result": True, "user": user_data}
        if not user_data:
            result["result"] = False
        return result


@route.post("/{id}/follow", response_model=schemas.Result, name="Подписаться")
async def subscribe_to_user(id: int, user: dep.ApiKey):
    """Пользователь подписывается на другого пользователя."""


@route.delete("/{id}/follow", response_model=schemas.Result, name="Отписаться")
async def unsubscribe_to_user(id: int, user: dep.ApiKey):
    """Пользователь отписывается от другого пользователя."""
