from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.session import create_engine, create_session_factory


settings = Settings()
engine: AsyncEngine = create_engine(settings.database_url)
session_factory: async_sessionmaker[AsyncSession] = create_session_factory(engine)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def dispose_engine() -> None:
    await engine.dispose()
