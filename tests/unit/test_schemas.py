import pytest
from pydantic import ValidationError

from src.modules.auth.schema import RegisterRequest, TokenPair
from src.modules.users.schema import UserRead

VALID_REGISTER = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "supersecret123",
}


class TestRegisterRequest:
    def test_valid(self):
        data = RegisterRequest(**VALID_REGISTER)

        assert data.email == VALID_REGISTER["email"]

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("first_name", ""),
            ("first_name", "a" * 21),
            ("last_name", ""),
            ("last_name", "a" * 21),
            ("email", "not-an-email"),
            ("email", "a" * 40 + "@example.com"),
            ("password", "short"),
            ("password", "a" * 129),
        ],
    )
    def test_invalid(self, field, value):
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**{**VALID_REGISTER, field: value})

        assert exc_info.value.errors()[0]["loc"] == (field,)


def test_token_pair_default_type():
    tokens = TokenPair(access_token="a", refresh_token="r")

    assert tokens.token_type == "bearer"


class TestUserRead:
    def test_from_orm_object(self, user):
        data = UserRead.model_validate(user)

        assert data.id == user.id
        assert data.email == user.email
        assert data.role == user.role

    def test_password_hash_not_exposed(self, user):
        data = UserRead.model_validate(user).model_dump()

        assert "password_hash" not in data
