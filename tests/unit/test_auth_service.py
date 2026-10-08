from datetime import timedelta

import pytest
from fastapi import HTTPException, status

from src.modules.auth.schema import (
    AccessToken,
    LoginRequest,
    RegisterRequest,
    TokenPair,
)
from src.modules.auth.service import credentials_exception
from src.modules.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    encode_jwt,
    verify_password,
)
from tests.conftest import PASSWORD


def assert_unauthorized(exc: HTTPException, detail: str) -> None:
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.detail == detail
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_credentials_exception_default():
    assert_unauthorized(credentials_exception(), "Could not validate credentials")


class TestRegister:
    @pytest.fixture
    def data(self) -> RegisterRequest:
        return RegisterRequest(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password=PASSWORD,
        )

    async def test_email_already_exists(self, auth_service, mock_repo, user, data):
        mock_repo.get_by_email.return_value = user

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(data)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        mock_repo.create.assert_not_called()

    async def test_success(self, auth_service, mock_repo, user, data):
        mock_repo.get_by_email.return_value = None
        mock_repo.create.return_value = user

        result = await auth_service.register(data)

        assert result is user
        kwargs = mock_repo.create.call_args.kwargs
        assert kwargs["first_name"] == data.first_name
        assert kwargs["last_name"] == data.last_name
        assert kwargs["email"] == data.email
        assert "password" not in kwargs
        assert kwargs["password_hash"] != PASSWORD
        assert verify_password(PASSWORD, kwargs["password_hash"])


class TestLogin:
    async def test_user_not_found(self, auth_service, mock_repo):
        mock_repo.get_by_email.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(
                LoginRequest(email="nobody@example.com", password=PASSWORD)
            )

        assert_unauthorized(exc_info.value, "Invalid email or password")

    async def test_wrong_password(self, auth_service, mock_repo, user):
        mock_repo.get_by_email.return_value = user

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(
                LoginRequest(email=user.email, password="wrong-password")
            )

        assert_unauthorized(exc_info.value, "Invalid email or password")

    async def test_success(self, auth_service, mock_repo, user):
        mock_repo.get_by_email.return_value = user

        result = await auth_service.login(
            LoginRequest(email=user.email, password=PASSWORD)
        )

        assert isinstance(result, TokenPair)
        assert result.token_type == "bearer"
        assert decode_jwt(result.access_token)["type"] == "access"
        assert decode_jwt(result.refresh_token)["type"] == "refresh"


class TestGetUserFromToken:
    async def test_success(self, auth_service, mock_repo, user):
        mock_repo.get_by_id.return_value = user

        result = await auth_service.get_user_from_token(
            create_access_token(user), "access"
        )

        assert result is user
        mock_repo.get_by_id.assert_awaited_once_with(user.id)

    async def test_expired(self, auth_service):
        token = encode_jwt({"sub": "1", "type": "access"}, timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user_from_token(token, "access")

        assert_unauthorized(exc_info.value, "Token has expired")

    async def test_invalid(self, auth_service):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user_from_token("not-a-jwt", "access")

        assert_unauthorized(exc_info.value, "Invalid token")

    @pytest.mark.parametrize(
        ("create_token", "expected_type"),
        [
            (create_refresh_token, "access"),
            (create_access_token, "refresh"),
        ],
    )
    async def test_wrong_type(self, auth_service, user, create_token, expected_type):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user_from_token(create_token(user), expected_type)

        assert_unauthorized(exc_info.value, "Invalid token type")

    @pytest.mark.parametrize(
        "payload",
        [
            {"type": "access"},
            {"sub": "abc", "type": "access"},
        ],
        ids=["no-sub", "non-int-sub"],
    )
    async def test_bad_sub(self, auth_service, mock_repo, payload):
        token = encode_jwt(payload, timedelta(minutes=5))

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user_from_token(token, "access")

        assert_unauthorized(exc_info.value, "Invalid token")
        mock_repo.get_by_id.assert_not_called()

    async def test_user_not_found(self, auth_service, mock_repo, user):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_user_from_token(create_access_token(user), "access")

        assert_unauthorized(exc_info.value, "User not found")


class TestRefresh:
    async def test_success(self, auth_service, mock_repo, user):
        mock_repo.get_by_id.return_value = user

        result = await auth_service.refresh(create_refresh_token(user))

        assert isinstance(result, AccessToken)
        payload = decode_jwt(result.access_token)
        assert payload["type"] == "access"
        assert payload["sub"] == str(user.id)

    async def test_access_token_rejected(self, auth_service, user):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh(create_access_token(user))

        assert_unauthorized(exc_info.value, "Invalid token type")
