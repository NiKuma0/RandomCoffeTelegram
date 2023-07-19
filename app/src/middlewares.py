from aiogram import types, Dispatcher
from peewee import DoesNotExist

from app.db.models import User
from app.config import Config


async def get_user_middleware(handler, event, data):
    tg_user: types.User = data["event_from_user"]
    config: Config = data["config"]
    user: User | None
    try:
        user = User.get(User.teleg_id == tg_user.id)
        user.teleg_username = tg_user.username
        user.full_name = tg_user.full_name
        user.is_admin = user.teleg_id in config.ADMINS
        user.save(only=(User.teleg_username, User.first_name, User.last_name, User.is_admin))
    except DoesNotExist:
        user = None
    data["model_user"] = user
    return await handler(event, data)


async def get_answer_func(handler, event: types.Update, data):
    match (update := event.event):
        case types.Message():
            data["answer"] = update.answer
        case types.CallbackQuery():
            data["answer"] = update.message.edit_text
        case _ if data['event_from_user']:
            return lambda *args, **kwargs: data['bot'].send_message(
                chat_id=data['event_from_user'].id, *args, **kwargs
            )
    return await handler(event, data)


def register_middlewares(dp: Dispatcher):
    dp.update.outer_middleware()(get_user_middleware)
    dp.update.outer_middleware()(get_answer_func)
