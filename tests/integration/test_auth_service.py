import pytest
from fastapi import HTTPException, status

from src.modules.auth.schema import LoginRequest, RegisterRequest
from src.modules.auth.utils import create_access_token, verify_password
from tests.conftest import PASSWORD

REGISTER_DATA = RegisterRequest(
    first_name="Jane",
    last_name="Doe",
    email="jane@example.com",
    password=PASSWORD,
)


class TestRegister:
    async def test_saves_user_with_hashed_password(self, service, repo):
        user = await service.register(REGISTER_DATA)

        saved = await repo.get_by_email(REGISTER_DATA.email)
        assert saved is not None
        assert saved.id == user.id
        assert saved.password_hash != PASSWORD
        assert verify_password(PASSWORD, saved.password_hash)

    async def test_duplicate_email(self, service):
        await service.register(REGISTER_DATA)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(REGISTER_DATA)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT


async def test_register_login_refresh_flow(service):
    user = await service.register(REGISTER_DATA)

    tokens = await service.login(
        LoginRequest(email=REGISTER_DATA.email, password=PASSWORD)
    )
    current = await service.get_user_from_token(tokens.access_token, "access")
    assert current.id == user.id

    new_access = await service.refresh(tokens.refresh_token)
    current = await service.get_user_from_token(new_access.access_token, "access")
    assert current.id == user.id


async def test_login_wrong_password(service, db_user):
    with pytest.raises(HTTPException) as exc_info:
        await service.login(LoginRequest(email=db_user.email, password="wrong-pass"))

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_token_of_deleted_user(service, session, db_user):
    token = create_access_token(db_user)
    await session.delete(db_user)
    await session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_user_from_token(token, "access")

    assert exc_info.value.detail == "User not found"
