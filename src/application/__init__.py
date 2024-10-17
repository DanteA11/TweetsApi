from fastapi import FastAPI

from .routes import medias, tweets, users
from .utils import update_schema_name


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(root_path="/api")

    app.include_router(tweets.route)
    app.include_router(medias.route)
    app.include_router(users.route)

    update_schema_name(app, medias.add_file, "Media")

    return app
