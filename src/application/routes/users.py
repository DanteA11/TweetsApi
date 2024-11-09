"""Реализация /users."""

from fastapi import APIRouter

from .. import dependencies as dep
from .. import schemas

route = APIRouter(prefix="/users", tags=["users"])


@route.get("/me", response_model=schemas.Users, name="Мой профиль")
async def get_me(user: dep.ApiKey, crud: dep.crud_controller):
    """Пользователь запрашивает информацию о своем профиле."""
    user_data = await crud.get_full_user_info(user.id, user=user)
    result = {"result": True, "user": user_data}
    return result


@route.get("/{id}", response_model=schemas.Users, name="Профиль по ID")
async def get_user_by_id(id: int, user: dep.ApiKey, crud: dep.crud_controller):
    """Пользователь запрашивает информацию о профиле другого пользователя по ID."""
    user_data = await crud.get_full_user_info(id)
    result = {"result": True, "user": user_data}
    if not user_data:
        result["result"] = False
    return result


@route.post("/{id}/follow", response_model=schemas.Result, name="Подписаться")
async def subscribe_to_user(
    id: int, user: dep.ApiKey, crud: dep.crud_controller
):
    """Пользователь подписывается на другого пользователя."""
    result = await crud.add_subscribe(user.id, id)
    return {"result": result}


@route.delete("/{id}/follow", response_model=schemas.Result, name="Отписаться")
async def unsubscribe_to_user(
    id: int, user: dep.ApiKey, crud: dep.crud_controller
):
    """Пользователь отписывается от другого пользователя."""
    result = await crud.drop_subscribe(user.id, id)
    return {"result": result}
