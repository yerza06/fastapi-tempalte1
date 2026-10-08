from datetime import timedelta

import jwt
import pytest

from src.core.config import settings
from src.modules.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    encode_jwt,
    hash_password,
    verify_password,
)
from tests.conftest import PASSWORD


class TestPasswordHashing:
    def test_hash_differs_from_password(self, password_hash):
        assert password_hash != PASSWORD

    def test_same_password_gives_different_hashes(self, password_hash):
        assert hash_password(PASSWORD) != password_hash

    def test_verify_correct_password(self, password_hash):
        assert verify_password(PASSWORD, password_hash) is True

    def test_verify_wrong_password(self, password_hash):
        assert verify_password("wrong-password", password_hash) is False


class TestJWT:
    def test_round_trip(self):
        token = encode_jwt({"sub": "1", "foo": "bar"}, timedelta(minutes=5))
        payload = decode_jwt(token)

        assert payload["sub"] == "1"
        assert payload["foo"] == "bar"
        assert "iat" in payload
        assert "exp" in payload

    def test_exp_matches_delta(self):
        token = encode_jwt({"sub": "1"}, timedelta(minutes=5))
        payload = decode_jwt(token)

        assert payload["exp"] - payload["iat"] == 5 * 60

    def test_expired_token(self):
        token = encode_jwt({"sub": "1"}, timedelta(seconds=-1))

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_jwt(token)

    def test_wrong_secret(self):
        token = jwt.encode(
            {"sub": "1"},
            "another-secret-key-at-least-32-bytes",
            algorithm=settings.auth.ALGORITHM,
        )

        with pytest.raises(jwt.InvalidSignatureError):
            decode_jwt(token)

    def test_garbage_token(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_jwt("not-a-jwt")


class TestCreateTokens:
    def test_access_token(self, user):
        payload = decode_jwt(create_access_token(user))

        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["type"] == "access"
        assert payload["exp"] - payload["iat"] == (
            settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def test_refresh_token(self, user):
        payload = decode_jwt(create_refresh_token(user))

        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["type"] == "refresh"
        assert payload["exp"] - payload["iat"] == (
            settings.auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
