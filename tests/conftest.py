from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.auth.service import AuthService
from src.modules.auth.utils import hash_password
from src.modules.users.models import User, UserRole
from src.modules.users.repository import UserRepository

PASSWORD = "supersecret123"


@pytest.fixture(scope="session")
def password_hash() -> str:
    # NOTE: argon2 медленный, поэтому хешируем один раз на всю сессию
    return hash_password(PASSWORD)


@pytest.fixture
def user(password_hash: str) -> User:
    return User(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password_hash=password_hash,
        role=UserRole.USER,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def auth_service(mock_repo: AsyncMock) -> AuthService:
    service = AuthService(session=MagicMock())
    service.users = mock_repo
    return service
