import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.schema import (
    AccessToken,
    LoginRequest,
    RegisterRequest,
    TokenPair,
)
from src.modules.auth.utils import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    hash_password,
    verify_password,
)
from src.modules.users.models import User
from src.modules.users.repository import UserRepository


def credentials_exception(
    detail: str = "Could not validate credentials",
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    @staticmethod
    def _issue_tokens(user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user),
            refresh_token=create_refresh_token(user),
        )

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        return await self.users.create(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
        )

    async def login(self, data: LoginRequest) -> TokenPair:
        user = await self.users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise credentials_exception("Invalid email or password")

        return self._issue_tokens(user)

    async def get_user_from_token(self, token: str, token_type: TokenType) -> User:
        try:
            payload = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            raise credentials_exception("Token has expired")
        except jwt.InvalidTokenError:
            raise credentials_exception("Invalid token")

        if payload.get("type") != token_type:
            raise credentials_exception("Invalid token type")

        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            raise credentials_exception("Invalid token")

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise credentials_exception("User not found")

        return user

    async def refresh(self, refresh_token: str) -> AccessToken:
        user = await self.get_user_from_token(refresh_token, "refresh")
        return AccessToken(access_token=create_access_token(user))
