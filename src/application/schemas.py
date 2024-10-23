"""Схемы валидации."""

from pydantic import BaseModel


class BaseId(BaseModel):
    """
    Базовая схема с id.

    :arg id: Идентификатор.
    """

    id: int


class BaseName(BaseModel):
    """
    Базовая схема с именем.

    :arg name: Имя.
    """

    name: str


class BaseResult(BaseModel):
    """
    Базовая схема с результатом.

    :arg result: Результат выполнения операции
    """

    result: bool


class Result(BaseResult):
    """Схема результата."""

    pass


class Author(BaseId, BaseName):
    """Схема автора."""

    pass


class Like(BaseName):
    """
    Схема отметки 'Нравится'.

    :arg user_id: Идентификатор пользователя.
    """

    user_id: int


class MediaResult(BaseResult):
    """
    Схема результата загрузки медиафайла.

    :arg media_id: Идентификатор медиафайла.
    """

    media_id: int


class TweetResult(BaseResult):
    """
    Результат отправки твита.

    :arg tweet_id: Идентификатор твита.
    """

    tweet_id: int = -1


class TweetIn(BaseModel):
    """
    Схема входящего твита.

    :arg tweet_data: Текст твита.
    :arg tweet_media_ids: Список идентификаторов твита.
    """

    tweet_data: str
    tweet_media_ids: list[int] | None = None


class TweetOut(BaseId):
    """
    Схема исходящего твита.

    :arg content: Текст твита.
    :arg attachments: Ссылки на вложения. # TODO Уточнить.
    :arg author: Автор твита.
    :arg likes: Список лайков.
    """

    content: str
    attachments: list[str]
    author: Author
    likes: list[Like]


class TweetError(BaseResult):
    """
    Схема ошибки при поиске твита.

    :arg error_type: Тип ошибки.
    :arg error_message: Сообщение об ошибке.
    """

    error_type: str
    error_message: str


class Tweets(BaseResult):
    """
    Схема результата поиска твитов.

    :arg tweets: Список твитов.
    """

    tweets: list[TweetOut]


class User(BaseId, BaseName):
    """
    Схема информации о пользователе.

    :arg followers: Подписчики.
    :arg following: Авторы, на которых подписан пользователь.
    """

    followers: list[Author]
    following: list[Author]


class Users(BaseResult):
    """
    Схема результата поиска пользователей.

    :arg user: Найденный пользователь.
    """

    user: User | None
