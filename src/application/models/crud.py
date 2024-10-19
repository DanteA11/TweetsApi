"""Функции для взаимодействия с базой данных."""

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ._models import Base, Subscribe, User


async def get_user_by_api_key(api_key: str, async_session: AsyncSession):
    """
    Запрашивает модель пользователя из базы данных с помощью ключа авторизации.

    :param api_key: Код для авторизации пользователя.
    :param async_session: Экземпляр сессии.

    :return: Модель User по api_key, если не найден, возвращает None.
    """
    query = select(User).filter(User.api_key.has(key=api_key))
    result = await async_session.execute(query)
    user: User | None = result.scalars().first()  # type: ignore
    return user


async def get_full_user_info(
    user_id: int, async_session: AsyncSession, *, user: User | None = None
):
    """
    Запрашивает из базы полную информацию о пользователе.

    :param user_id: ID пользователя для поиска.
    :param async_session: Экземпляр сессии.
    :param user: Экземпляр User. Необязательный параметр.
    При добавлении не запрашивается в БД.

    :return: Словарь с данными пользователя:
    {'id': int, 'name': str, 'followers': [User], 'following': [User]}.
    Если пользователь не найден и не передан как параметр User, возвращает None.
    """
    user = user or await _get_by_id(user_id, User, async_session)
    if not user:
        return
    user_data = user.to_dict()
    query_following = (
        select(User)
        .join(Subscribe, User.id == Subscribe.author_id)
        .filter(User.id != user_id)
    )
    following = await async_session.execute(query_following)
    query_followers = (
        select(User)
        .join(Subscribe, User.id == Subscribe.follower_id)
        .filter(User.id != user_id)
    )
    followers = await async_session.execute(query_followers)

    user_data["following"] = following.scalars().all()
    user_data["followers"] = followers.scalars().all()

    return user_data


async def _get_by_id(id_: int, model: type[Base], async_session: AsyncSession):
    """
    Запрашивает модель из базы данных по id.

    :param id_: ID записи.
    :param model: Модель ORM, обязательно с полем id.
    :param async_session: Экземпляр сессии.

    :return: Объект переданной модели, если не найдено, то None.
    """
    query = select(model).filter(model.id == id_)  # type: ignore
    result = await async_session.execute(query)
    return result.scalars().first()


async def add_subscribe(
    user_id: int, author_id: int, async_session: AsyncSession
):
    """
    Создает подписку на пользователя.

    :param user_id: ID пользователя, который подписывается.
    :param author_id: ID пользователя, на которого подписываются
    :param async_session: Экземпляр сессии.

    :return: True, если подписка выполнена, иначе False.
    """
    if user_id == author_id:
        return False
    user = await _get_by_id(author_id, User, async_session)
    if not user:
        return False
    subscribe = Subscribe(follower_id=user_id, author_id=author_id)
    async_session.add(subscribe)
    try:
        await async_session.commit()
    except IntegrityError:
        await async_session.rollback()
        return False
    return True


async def drop_subscribe(
    user_id: int, author_id: int, async_session: AsyncSession
):
    """
    Удаляет подписку на пользователя.

    :param user_id: ID пользователя, который отписывается.
    :param author_id: ID пользователя, от которого отписываются.
    :param async_session: Экземпляр сессии.

    :return: Если автор сам пользователь или не существует,
     возвращает False, иначе True.
    """
    if user_id == author_id:
        return False
    user = await _get_by_id(author_id, User, async_session)
    if not user:
        return False
    query = delete(Subscribe).filter(
        Subscribe.follower_id == user_id, Subscribe.author_id == author_id
    )
    await async_session.execute(query)
    await async_session.commit()
    return True
