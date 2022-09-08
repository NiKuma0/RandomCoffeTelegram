from src.auth import auth_router
from src.matching import match_router
from src.middlewares import register_middlewares
from src.admin import admin_router

__all__ = (
    'auth_router',
    'match_router',
    'register_middlewares',
    'admin_router',
)
