from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

AUTOFLUSH = settings.db.AUTOFLUSH
EXPIRE_ON_COMMIT = settings.db.EXPIRE_ON_COMMIT


engine = create_async_engine(settings.db.sqlalchemy_url())
session_factory = async_sessionmaker(
    engine, autoflush=AUTOFLUSH, expire_on_commit=EXPIRE_ON_COMMIT
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]
