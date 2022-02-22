from pprint import pprint
from aiogram import types

from db.models import User
from config import DP, BOT


async def get_user(user: types.User) -> User:
    try:
        user = User.get_by_id(user.id)
    except User.DoesNotExist:
        user = None
    return user


async def get_user_middleware(handler, event, data):
    data['model_user'] = await get_user(data['event_from_user']) 
    return await handler(event, data)


async def send_message(id):
    async def wrapper(*args, **kwargs):
        return BOT.send_message(id, *args, **kwargs)
    return wrapper

async def get_answer_func(handler, event: types.Update, data):
    match (update := event.event):
        case types.Message():
            data['answer'] = update.answer
        case types.CallbackQuery():
            data['answer'] = update.message.edit_text
        case _:
            data['answer'] = await send_message(data['event_from_user'].id)
    return await handler(event, data)


def register_middlewares():
    DP.update.outer_middleware()(get_user_middleware)
    DP.update.outer_middleware()(get_answer_func)
