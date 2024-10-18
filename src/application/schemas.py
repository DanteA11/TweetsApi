from pydantic import BaseModel


class BaseId(BaseModel):
    id: int


class BaseName(BaseModel):
    name: str


class BaseResult(BaseModel):
    result: bool


class Result(BaseResult):
    pass


class Author(BaseId, BaseName):
    pass


class Like(BaseName):
    user_id: int


class MediaResult(BaseResult):
    media_id: int


class TweetResult(BaseResult):
    tweet_id: int


class TweetIn(BaseModel):
    tweet_data: str
    tweet_media_ids: list[int] | None = None


class TweetOut(BaseId):
    content: str
    attachments: list[str]
    author: Author
    likes: list[Like]


class TweetError(BaseResult):
    error_type: str
    error_message: str


class Tweets(BaseResult):
    tweets: list[TweetOut]


class User(BaseId, BaseName):
    followers: list[Author]
    following: list[Author]


class Users(BaseResult):
    user: User | None
