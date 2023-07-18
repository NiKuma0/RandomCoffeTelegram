from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import BaseFilter
from peewee import DoesNotExist

from app.db.models import User


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message, model_user: User):
        if not model_user or not model_user.is_admin:
            await message.answer("У вас недостаточно прав")
            return False
        return True


class ErrorFilterUserDoesNotExist(BaseFilter):
    """
    Временный класс.
    Пока commit [Error handlers not working #822] (aiogram) не войдёт в версию PyPi
    """

    async def __call__(self, message: types.Message, exception: Exception):
        return isinstance(exception, DoesNotExist)


class Order(StatesGroup):
    waiting_for_password = State()
    about_bot = State()
    waiting_for_real_name = State()
    set_profession = State()
    start = State()
