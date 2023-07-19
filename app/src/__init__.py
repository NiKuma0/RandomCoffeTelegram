from aiogram import Router

from .auth import auth_router
from .matching import match_router
from .middlewares import register_middlewares
from .admin import admin_router


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
