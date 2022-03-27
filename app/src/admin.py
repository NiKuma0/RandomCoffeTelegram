import asyncio
import logging

from aiogram import types, Router
from aiogram.dispatcher.filters import BaseFilter, command

from src.matching import ask_pairs, get_feedback
from db.models import User, Pair, Profession

types.InputMessageContent
admin_router = Router()
logger = logging.getLogger(__name__)


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message, model_user):
        if not model_user or not model_user.is_admin:
            await message.answer('У вас недостаточно прав')
            return False
        return True


class ErrorFilterUserDoesNotExist(BaseFilter):
    '''
    Временный класс.
    Пока commit [Error handlers not working #822] (aiogram) не войдёт в версию PyPi
    '''
    async def __call__(self, message: types.Message, exception):
        return isinstance(exception, User.DoesNotExist)


admin_router.message.bind_filter(AdminFilter)


async def get_user(username: str, async_func_answer_error=None) -> User:
    error_msg = f'Пользаватель, @{username}, не найден. Возможно он не запускал бот.'
    try:
        return User.get(User.teleg_username == username)
    except User.DoesNotExist as error:
        if not async_func_answer_error:
            raise error
        await async_func_answer_error(error_msg)
        raise error


@admin_router.message(commands='add_admin')
async def add_admin(message, command: command.CommandObject):
    if not command.args:
        return await message.answer('Не хватает аттрибутов.\n/add_admin [username нового админа]')
    args = command.args.split()
    users = await asyncio.gather(*map(get_user, args))
    for user in users:
        user.is_admin = True
        user.save()
    await message.answer((
        f'Пользаватель, @{args[0]}, успешно посвящён в администраторы!' 
        if len(command.args) == 1 else
        f'Пользаватели успешно посвящанны в администраторы!\n{" @".join(args)}'
    ))


@admin_router.message(commands='add_profession')
async def add_profession(message: types.Message, command: command.CommandObject):
    if not command.args:
        return await message.answer(
            'Нехватает атрибутов.\n'
            '   /add_profession [Название профессии]'
        )
    Profession.create(name=command.args)
    await message.answer(
        'Успешно!'
    )


@admin_router.message(commands='ask_pairs')
async def admin_ask_pairs(message):
    await message.answer('Запустил!')
    await ask_pairs()


@admin_router.message(commands='ask_pair')
async def admin_ask_pair(message: types.Message, command: command.CommandObject):
    if not command.args or len(args := command.args.split()) != 2:
        return await message.answer(
            'Комманда принимает только 2 аргумента.\n'
            '   /ask_pair [hr] [респондент]  # Порядок важен!'
        )
    hr, respondent = await asyncio.gather(*map(get_user, args))
    try:
        pair = Pair.get(Pair.hr == hr, Pair.respondent == respondent)
    except Pair.DoesNotExist:
        return await message.answer(
            'Пара не найдена. Проверьте порядок:\n'
            '   /ask_pair [hr] [респондент]  # Сночало hr потом респондент'
        )
    await message.answer('Успешно!')
    await get_feedback(pair)


@admin_router.errors(ErrorFilterUserDoesNotExist())
async def user_not_exist(update: types.Update, exception):
    await update.message.answer('Пользаватель не найден')
