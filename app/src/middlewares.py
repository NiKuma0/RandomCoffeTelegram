from aiogram import types, Dispatcher
from peewee_async import Manager

from db.models import User
from db import Manager
from config import BOT


async def get_user_middleware(handler, event, data):
    objects = Manager()
    tg_user: types.User = data["event_from_user"]
    try:
        user: User = await objects.get(User, User.teleg_id == tg_user.id)
        user.teleg_username = tg_user.username
        user.full_name = tg_user.full_name
        await objects.update(user, only=("teleg_username", "full_name"))
    except User.DoesNotExist:
        user = None
    data["model_user"] = user
    return await handler(event, data)


async def send_message(chat_id):
    async def wrapper(*args, **kwargs):
        return BOT.send_message(chat_id=chat_id, *args, **kwargs)

    return wrapper


async def get_answer_func(handler, event: types.Update, data):
    match (update := event.event):
        case types.Message():
            data["answer"] = update.answer
        case types.CallbackQuery():
            data["answer"] = update.message.edit_text
        case _:
            data["answer"] = await send_message(data["event_from_user"].id)
    return await handler(event, data)


def register_middlewares(dp: Dispatcher):
    dp.update.outer_middleware()(get_user_middleware)
    dp.update.outer_middleware()(get_answer_func)
