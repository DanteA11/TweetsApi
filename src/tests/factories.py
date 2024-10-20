from itertools import count

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import Faker, LazyAttribute, SubFactory
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import scoped_session

from application.dependencies import AsyncEngineGetter, get_async_session_maker
from application.models import ApiKey, Subscribe, User


def get_session():
    """Возвращает экземпляр асинхронной сессии."""
    engine_getter = AsyncEngineGetter()
    engine: AsyncEngine = engine_getter.engine
    async_session_maker = get_async_session_maker(engine)
    session_ = scoped_session(async_session_maker)

    return session_


counter = count(1)
session = get_session()


class ApiKeyFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = ApiKey
        sqlalchemy_session = session

    key = LazyAttribute(lambda o: f"key-{next(counter)}")


class UserFactory(AsyncSQLAlchemyFactory):
    class Meta:
        model = User
        sqlalchemy_session = session

    name = Faker("name")
    api_key = SubFactory(ApiKeyFactory)
