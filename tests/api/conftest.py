from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import get_session
from src.main import app
from src.modules.users.models import User
from tests.conftest import PASSWORD


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    # NOTE: Подменяем сессию приложения на тестовую, чтобы запросы шли в тестовую
    # базу и откатывались после каждого теста
    app.dependency_overrides[get_session] = lambda: session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def tokens(client: AsyncClient, db_user: User) -> dict[str, str]:
    response = await client.post(
        "/auth/login", json={"email": db_user.email, "password": PASSWORD}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
