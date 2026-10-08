from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.core.config import settings
from src.core.database.base import Base
from src.modules.auth.service import AuthService
from src.modules.auth.utils import hash_password
from src.modules.users.models import User
from src.modules.users.repository import UserRepository
from tests.conftest import PASSWORD

# NOTE: Тесты работают с отдельной базой "<DATABASE>_test", рабочая база не трогается
test_db = settings.db.model_copy(update={"DATABASE": f"{settings.db.DATABASE}_test"})


async def create_test_database() -> None:
    admin_engine = create_async_engine(
        settings.db.sqlalchemy_url(), isolation_level="AUTOCOMMIT"
    )
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": test_db.DATABASE},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{test_db.DATABASE}"'))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    try:
        await create_test_database()
    except OSError as e:
        pytest.skip(f"PostgreSQL недоступен: {e}")

    engine = create_async_engine(test_db.sqlalchemy_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    # NOTE: Каждый тест выполняется внутри транзакции, которая в конце откатывается.
    # commit() внутри репозитория фиксирует только SAVEPOINT, поэтому тесты не видят
    # данные друг друга
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest.fixture
def repo(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def service(session: AsyncSession) -> AuthService:
    return AuthService(session)


@pytest.fixture
async def db_user(repo: UserRepository) -> User:
    return await repo.create(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password_hash=hash_password(PASSWORD),
    )
