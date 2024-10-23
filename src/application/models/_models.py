from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

__all__ = [
    "Base",
    "ApiKey",
    "User",
    "Subscribe",
    "Like",
    "Tweet",
    "Media",
]


class ApiKey(Base):
    """Ключ для авторизации пользователя."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True)

    user = relationship("User", back_populates="api_key", uselist=False)


class User(Base):
    """Пользователь."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    key_id = Column(Integer, ForeignKey("api_keys.id"))

    api_key = relationship("ApiKey", back_populates="user", uselist=False)
    medias = relationship("Media", back_populates="user")
    likes = relationship("Like", back_populates="user")
    tweets = relationship("Tweet", back_populates="author")


class Subscribe(Base):
    """Подписки."""

    __tablename__ = "subscribes"

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id"), primary_key=True)


class Like(Base):
    """Отметки 'Нравится'."""

    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True
    )

    user = relationship("User", back_populates="likes", uselist=False)
    tweet = relationship("Tweet", back_populates="likes", uselist=False)


class Tweet(Base):
    """Твиты."""

    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    likes = relationship("Like", back_populates="tweet")
    author = relationship("User", back_populates="tweets", uselist=False)
    medias = relationship("Media", back_populates="tweet")


class Media(Base):
    """Медиафайлы."""

    __tablename__ = "medias"

    id = Column(Integer, primary_key=True)
    file_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="medias", uselist=False)
    tweet = relationship("Tweet", back_populates="medias", uselist=False)
