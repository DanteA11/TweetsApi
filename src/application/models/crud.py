from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base, Subscribe, User


async def get_user_by_api_key(api_key: str, async_session: AsyncSession):
    query = select(User).filter(User.api_key.has(key=api_key))
    result = await async_session.execute(query)
    user: User = result.scalars().first()  # type: ignore
    return user


async def get_full_user_info(
    user_id: int, async_session: AsyncSession, *, user: User | None = None
):
    user = user or await _get_by_id(user_id, User, async_session)
    if not user:
        return
    user_data = user.to_dict()
    query_following = (
        select(User)
        .filter(User.id == user_id)
        .join(Subscribe, User.id == Subscribe.follower_id)
    )
    following = await async_session.execute(query_following)
    query_follower = (
        select(User)
        .filter(User.id == user_id)
        .join(Subscribe, User.id == Subscribe.author_id)
    )
    followers = await async_session.execute(query_follower)

    user_data["following"] = following.scalars().all()
    user_data["followers"] = followers.scalars().all()

    return user_data


async def _get_by_id(id_: int, model: type[Base], async_session: AsyncSession):
    query = select(model).filter(model.id == id_)
    result = await async_session.execute(query)
    return result.scalars().first()
