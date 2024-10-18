from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from .database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True)

    user = relationship("User", back_populates="api_key", uselist=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    key_id = Column(Integer, ForeignKey("api_keys.id"))

    api_key = relationship("ApiKey", back_populates="user", uselist=False)
    media = relationship("Media", back_populates="user")
    like = relationship("Like", back_populates="user")


class Subscribe(Base):
    __tablename__ = "subscribes"

    follower_id = Column(Integer, primary_key=True)
    author_id = Column(Integer, primary_key=True)


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), primary_key=True)

    user = relationship("User", back_populates="like")
    tweet = relationship("Tweet", back_populates="like")


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    like = relationship("Like", back_populates="tweet")

    _tweet_media = relationship("TweetMedia", back_populates="tweet")
    media = association_proxy("_tweet_media", "media")


class Media(Base):
    __tablename__ = "medias"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="media")
    _tweet_media = relationship("TweetMedia", back_populates="media")
    tweet = association_proxy("_tweet_media", "tweet")


class TweetMedia(Base):
    __tablename__ = "tweet_medias"

    media_id = Column(Integer, ForeignKey("medias.id"), primary_key=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True
    )

    tweet = relationship("Tweet", back_populates="_tweet_media", uselist=False)
    media = relationship("Media", back_populates="_tweet_media", cascade="delete")
