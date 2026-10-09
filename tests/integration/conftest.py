import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.service import AuthService
from src.modules.users.repository import UserRepository


@pytest.fixture
def repo(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture
def service(session: AsyncSession) -> AuthService:
    return AuthService(session)
