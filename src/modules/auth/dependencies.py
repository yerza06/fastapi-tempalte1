from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.database.session import Session
from src.modules.auth.service import AuthService
from src.modules.users.models import User

bearer_scheme = HTTPBearer()


def get_auth_service(session: Session) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    service: AuthServiceDep,
) -> User:
    return await service.get_user_from_token(credentials.credentials, "access")


CurrentUser = Annotated[User, Depends(get_current_user)]
