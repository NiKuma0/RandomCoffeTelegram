from aiogram import types

from db.models import User
from config import DP


async def get_user(user: types.User) -> User:
    try:
        user = User.get_by_id(user.id)
    except User.DoesNotExist:
        user = None
    return user


async def get_user_middleware(handler, event, data):
    data['model_user'] = await get_user(data['event_from_user']) 
    return await handler(event, data)


def register_middlewares():
    DP.update.outer_middleware()(get_user_middleware)
