from fastapi import APIRouter, status

from src.modules.auth.dependencies import AuthServiceDep, CurrentUser
from src.modules.auth.schema import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from src.modules.users.schema import UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, service: AuthServiceDep):
    return await service.register(data)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginRequest, service: AuthServiceDep):
    return await service.login(data)


@router.post("/refresh", response_model=AccessToken)
async def refresh(data: RefreshRequest, service: AuthServiceDep):
    return await service.refresh(data.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user
