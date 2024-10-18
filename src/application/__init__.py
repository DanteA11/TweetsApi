from fastapi import FastAPI

from .dependencies import Lifespan
from .routes import medias, tweets, users
from .utils import update_schema_name


def create_app(*, drop_all: bool = False) -> FastAPI:
    lifespan = Lifespan(drop_all=drop_all)
    app: FastAPI = FastAPI(root_path="/api", lifespan=lifespan, title="TweetsApi")

    app.include_router(tweets.route)
    app.include_router(medias.route)
    app.include_router(users.route)

    update_schema_name(app, medias.add_file, "Media")

    return app
