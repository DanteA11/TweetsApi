from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore

    def __repr__(self):
        res = ", ".join([f"{k}={v}" for k, v in self.to_dict().items()])
        return f"{type(self).__name__}({res})"


def get_async_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url)
    return engine


async def start_conn(engine: AsyncEngine, drop_all: bool = False):
    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def stop_conn(engine: AsyncEngine, drop_all: bool = False):
    if drop_all:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
