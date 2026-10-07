from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from pwdlib import PasswordHash

from src.core.config import settings
from src.modules.users.models import User

TokenType = Literal["access", "refresh"]

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def encode_jwt(payload: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    to_encode = {**payload, "iat": now, "exp": now + expires_delta}
    return jwt.encode(
        to_encode, settings.auth.SECRET_KEY, algorithm=settings.auth.ALGORITHM
    )


def decode_jwt(token: str) -> dict[str, Any]:
    return jwt.decode(
        token, settings.auth.SECRET_KEY, algorithms=[settings.auth.ALGORITHM]
    )


def _create_token(user: User, token_type: TokenType, expires_delta: timedelta) -> str:
    # NOTE: sub должен быть строкой, pyjwt это валидирует
    payload = {"sub": str(user.id), "type": token_type, "email": user.email}
    return encode_jwt(payload, expires_delta)


def create_access_token(user: User) -> str:
    return _create_token(
        user, "access", timedelta(minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user: User) -> str:
    return _create_token(
        user, "refresh", timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )
