from fastapi import APIRouter

from src.modules.auth.router import router as auth_router

MODULES = [
    auth_router,
]

modules_router = APIRouter()
for module in MODULES:
    modules_router.include_router(module)
