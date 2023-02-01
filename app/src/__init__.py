from aiogram import Router

from src.auth import auth_router
from src.matching import match_router
from src.middlewares import register_middlewares
from src.admin import admin_router


def register_routers(router: Router):
    router.include_router(auth_router)
    router.include_router(match_router)
    router.include_router(admin_router)


__all__ = (
    "auth_router",
    "match_router",
    "register_middlewares",
    "admin_router",
    "register_routers",
)
