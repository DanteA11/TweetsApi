"""Реализация взаимодействия с базой данных."""

import asyncio
import logging
import os.path
from typing import Any, Coroutine, TypeVar

import aiofiles
import aiofiles.os
from fastapi import UploadFile
from sqlalchemy import Column, delete, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from starlette.datastructures import URL

from ..settings import get_settings
from ._models import Base, Like, Media, Subscribe, Tweet, User

SETTINGS = get_settings()
logger = logging.getLogger(f"{SETTINGS.api_name}.{__name__}")
logger.setLevel(SETTINGS.log_level)
DEBUG = logger.isEnabledFor(
    logging.DEBUG  # https://docs.python.org/3/howto/logging.html#optimization
)
T = TypeVar("T", bound=Base)


class CrudController:
    """
    Класс для работы с базой данных.

    Все методы в классе асинхронные.

    :param session: Экземпляр асинхронной сессии.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.__async_session = session

    @property
    def async_session(self) -> AsyncSession:
        """Геттер сессии."""
        return self.__async_session

    async def get_user_by_api_key(self, api_key: str) -> User | None:
        """
        Запрашивает модель пользователя из базы данных с помощью ключа авторизации.

        :param api_key: Код для авторизации пользователя.

        :return: Модель User по api_key, если не найден, возвращает None.
        """
        if DEBUG:
            logger.debug("Получен api-key")
        query = select(User).filter(User.api_key.has(key=api_key))
        result = await self.async_session.execute(query)
        user: User | None = result.scalars().first()  # type: ignore
        if DEBUG:
            if user:
                logger.debug(f"Функция вернула пользователя: {user}")
            else:
                logger.debug("Пользователь не найден.")
        return user

    async def get_full_user_info(
        self,
        user_id: int | Column[int],
        *,
        user: User | None = None,
    ) -> dict[str, Any]:
        """
        Запрашивает из базы полную информацию о пользователе.

        :param user_id: ID пользователя для поиска.
        :param user: Экземпляр User. Необязательный параметр.
        При добавлении не запрашивается в БД.

        :return: Словарь с данными пользователя:
        {'id': int, 'name': str, 'followers': [User], 'following': [User]}.
        Если пользователь не найден и не передан как параметр User, возвращает {}.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, user={user}")
        user = user or await self.get_by_id(user_id, User, self.async_session)
        if not user:
            logger.info("Пользователь не найден")
            return {}
        user_data = user.to_dict()
        query_following = (
            select(User)
            .join(Subscribe, User.id == Subscribe.author_id)
            .filter(Subscribe.follower_id == user_id)
        )
        query_followers = (
            select(User)
            .join(Subscribe, User.id == Subscribe.follower_id)
            .filter(Subscribe.author_id == user_id)
        )

        following, followers = await asyncio.gather(
            self.async_session.execute(query_following),
            self.async_session.execute(query_followers),
        )

        user_data["following"] = following.scalars().all()
        user_data["followers"] = followers.scalars().all()
        if DEBUG:
            logger.debug(
                f"Функция вернула пользовательские данные: {user_data}"
            )
        return user_data

    @staticmethod
    async def get_by_id(
        id_: int | Column[int], model: type[T], async_session: AsyncSession
    ) -> T | None:
        """
        Запрашивает модель из базы данных по id.

        :param id_: ID записи.
        :param model: Модель ORM, обязательно с полем id.
        :param async_session: Экземпляр сессии.

        :return: Объект переданной модели, если не найдено, то None.
        """
        if DEBUG:
            logger.debug(f"id={id_}, model={model}")
        query = select(model).filter(model.id == id_)  # type: ignore
        result = await async_session.execute(query)
        res = result.scalars().first()
        if DEBUG:
            logger.debug(f"Функция вернула {res}")
        return res

    async def add_subscribe(
        self, user_id: int | Column[int], author_id: int
    ) -> bool:
        """
        Создает подписку на пользователя.

        :param user_id: ID пользователя, который подписывается.
        :param author_id: ID пользователя, на которого подписываются

        :return: True, если подписка выполнена, иначе False.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, author_id={author_id}")
        if user_id == author_id:
            logger.info(
                "user_id == author_id. Нельзя подписаться на самого себя"
            )
            return False
        subscribe = Subscribe(follower_id=user_id, author_id=author_id)
        self.async_session.add(subscribe)
        try:
            await self.async_session.commit()
        except IntegrityError:
            await self.async_session.rollback()
            logger.info("Подписка уже существует")
            return False
        return True

    async def drop_subscribe(
        self, user_id: int | Column[int], author_id: int
    ) -> bool:
        """
        Удаляет подписку на пользователя.

        :param user_id: ID пользователя, который отписывается.
        :param author_id: ID пользователя, от которого отписываются.

        :return: Если подписка удалена, возвращает True, иначе - False.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, author_id={author_id}")
        if user_id == author_id:
            logger.info(
                "user_id == author_id. Нельзя отписаться от самого себя"
            )
            return False
        query = delete(Subscribe).filter(
            Subscribe.follower_id == user_id, Subscribe.author_id == author_id
        )
        res = await self.async_session.execute(query)
        await self.async_session.commit()
        result = res.rowcount != 0
        if result:
            logger.info("Подписка деактивирована")
        else:
            logger.info("Подписка не существует")
        return result

    async def add_media(
        self, user_id: int | Column[int], media: UploadFile
    ) -> int:
        """
        Функция сохраняет медиафайл.

        :param user_id: ID пользователя
        :param media: Файл.

        :return: Возвращает медиа ID.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, media={media}")
        path = SETTINGS.media_path
        filename = media.filename or ""
        _, file_type = filename.split(".")
        media_ = Media(user_id=user_id, file_type=file_type)
        self.async_session.add(media_)
        _, res = await asyncio.gather(
            self.async_session.commit(), media.read()
        )
        media_id = await media_.awaitable_attrs.id
        res_path_coro = asyncio.to_thread(
            os.path.join, path, f"{media_id}.{file_type}"
        )
        res_path = await res_path_coro
        async with aiofiles.open(res_path, "wb") as file:
            await file.write(res)
        logger.info(f"Файл сохранен в {res_path}, media_id={media_id}")
        return media_id

    async def add_tweet(
        self,
        user_id: int | Column[int],
        tweet_data: str,
        tweet_media_ids: list[int],
    ) -> dict[str, bool | int]:
        """
        Функция добавляет новый твит.

        Переда добавлением информации о медиафайлах в твит,
         проверяет, чтобы id пользователя равнялось
        id автора медиафайла и чтобы медиафайл не участвовал в других твитах.

        :param user_id: ID пользователя.
        :param tweet_data: Текст твита.
        :param tweet_media_ids: ID медиафайлов.

        :return: Словарь с ключом result (type bool) и
        опциональным ключом tweet_id (type int).
        """
        if DEBUG:
            logger.debug(f"tweet_media_ids={tweet_media_ids}")
        tweet = Tweet(content=tweet_data, author_id=user_id)
        self.async_session.add(tweet)
        await self.async_session.flush()

        tweet_id = await tweet.awaitable_attrs.id
        if not tweet_media_ids:
            await self.async_session.commit()
            result = {"result": True, "tweet_id": tweet_id}
            logger.info(f"Твит сохранен. Функция вернула {result}")
            return result

        query = (
            update(Media)
            .filter(
                Media.user_id == user_id,
                Media.id.in_(tweet_media_ids),
                Media.tweet_id.is_(None),
            )
            .values(tweet_id=tweet_id)
        )
        res = await self.async_session.execute(query)
        if res.rowcount == 0:
            await self.async_session.rollback()
            result = {"result": False}
            logger.info(f"Не удалось сохранить твит. Функция вернула {result}")
            return result

        await self.async_session.commit()
        result = {"result": True, "tweet_id": tweet_id}
        logger.info(f"Твит сохранен. Функция вернула {result}")
        return result

    async def remove_tweet(
        self,
        user_id: int | Column[int],
        tweet_id: int,
    ) -> bool:
        """
        Удаляет твит и связанные медиафайлы.

        :param user_id: ID пользователя.
        :param tweet_id: ID твита.
        :return: Если твит найден и удален, возвращает True, иначе False
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, tweet_id={tweet_id}")
        query_medias = select(Media).filter(Media.tweet_id == tweet_id)
        media_task = asyncio.create_task(
            self.async_session.execute(query_medias)
        )
        path = SETTINGS.media_path
        query = delete(Tweet).filter(
            Tweet.id == tweet_id, Tweet.author_id == user_id
        )
        tasks: list[Coroutine[Any, Any, Any]] = [
            self.async_session.execute(query)
        ]
        medias_res = await media_task
        medias = medias_res.scalars().all()
        for media in medias:
            media_path_coro = asyncio.to_thread(
                os.path.join, path, media.id, media.file_type
            )
            media_path = await media_path_coro
            tasks.append(aiofiles.os.remove(media_path))
        results = await asyncio.gather(*tasks)
        await self.async_session.commit()
        res = results[0]
        result = res.rowcount != 0
        logger.info(f"Функция вернула {result}")
        return result

    async def create_like(
        self, user_id: int | Column[int], tweet_id: int
    ) -> bool:
        """
        Сохраняет информацию о лайке.

        :param user_id: ID пользователя.
        :param tweet_id: ID твита.

        :return: True, если лайк поставлен, иначе False.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, tweet_id={tweet_id}")
        like = Like(user_id=user_id, tweet_id=tweet_id)
        self.async_session.add(like)
        try:
            await self.async_session.commit()
        except IntegrityError:
            await self.async_session.rollback()
            logger.info("Не удалось поставить лайк")
            return False
        logger.info("Лайк поставлен")
        return True

    async def remove_like(
        self, user_id: int | Column[int], tweet_id: int
    ) -> bool:
        """
        Удаляет информацию о лайке.

        :param user_id: ID пользователя.
        :param tweet_id: ID твита.

        :return: True, если лайк удален, иначе False.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, tweet_id={tweet_id}")
        query = delete(Like).filter(
            Like.user_id == user_id, Like.tweet_id == tweet_id
        )
        res = await self.async_session.execute(query)
        await self.async_session.commit()
        result = res.rowcount != 0
        if result:
            logger.info("Лайк не найден")
        else:
            logger.info("Лайк удален")
        return result

    async def get_tweets_info(
        self,
        user_id: int | Column[int],
        base_url: str | URL,
    ) -> list[dict[str, Any]]:
        """
        Возвращает информацию о твитах, на которые подписан пользователь.

        :param user_id: ID пользователя.
        :param base_url: Базовый URL API.
        """
        if DEBUG:
            logger.debug(f"user_id={user_id}, base_url={base_url}")
        tweet_query = (
            select(Tweet)
            .join(Subscribe, Tweet.author_id == Subscribe.author_id)
            .join(Like, Tweet.id == Like.tweet_id)
            .filter(Subscribe.follower_id == user_id)
            .group_by(Tweet.id, Tweet.author_id, Tweet.content)
            .order_by(desc(count(Tweet.likes)))
        )
        result_tweets_task = asyncio.create_task(
            self.async_session.execute(tweet_query)
        )
        result = []
        result_tweets = await result_tweets_task
        tweets = result_tweets.scalars().all()
        if DEBUG:
            logger.debug(f"Получен список твитов: {tweets}")
        for tweet in tweets:
            media_task = asyncio.create_task(tweet.awaitable_attrs.medias)  # type: ignore
            res = tweet.to_dict()
            res["attachments"] = [
                f"{base_url}/{media.id}.{media.file_type}"
                for media in await media_task
            ]

            res["author"] = await tweet.awaitable_attrs.author
            likes_task = asyncio.create_task(tweet.awaitable_attrs.likes)  # type: ignore

            likes_data = []
            for like in await likes_task:
                user_task = asyncio.create_task(like.awaitable_attrs.user)  # type: ignore
                like_data = like.to_dict()
                user = await user_task
                like_data["name"] = user.name
                likes_data.append(like_data)

            res["likes"] = likes_data
            result.append(res)
        if DEBUG:
            logger.debug(f"Функция вернула: {result}")
        return result
