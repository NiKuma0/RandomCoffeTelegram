import asyncio

import aioschedule
from peewee import DoesNotExist
from aiogram import types, Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.filters.command import CommandObject, Command

from app.src.matching import ask_pairs, get_feedback
from app.db.models import User, Pair, Profession
from app.filters import AdminFilter


admin_router = Router()


@admin_router.startup()
async def startup(router: Router):
    router.message.filter(AdminFilter())


@admin_router.message(Command(commands="add_admin"))
async def add_admin(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer(
            "Не хватает аттрибутов.\n/add_admin [username нового админа]"
        )
    args = command.args.split()
    has_updated = User.update({User.is_admin: True}).where(User.teleg_username in args).execute()
    if has_updated == 0:
        return await message.answer("Ни один пользователь не найден!")
    if has_updated == 1 and len(args) == 1:
        return await message.answer(f"Пользователь, @{args[0]}, успешно посвящён в администраторы!")
    await message.answer(
        f"{has_updated} пользователей успешно посвящаенный в администраторы!"
    )


@admin_router.message(Command(commands="add_profession"))
async def add_profession(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer(
            "Нехватает атрибутов.\n"
            "\t/add_profession [Название профессии]"
        )
    Profession.create(name=command.args)
    await message.answer("Успешно!")


@admin_router.message(Command(commands="ask_pairs"))
async def admin_ask_pairs(message):
    await message.answer("Запустил!")
    await ask_pairs()


@admin_router.message(Command(commands="ask_pairs_forever"))
async def admin_ask_pairs_forever(message):
    await message.answer("Запустил!")
    aioschedule.every().day.at("12:00").do(ask_pairs)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


@admin_router.message(Command(commands="ask_pair"))
async def admin_ask_pair(message: types.Message, command: CommandObject):
    if not command.args or len(args := command.args.split()) != 2:
        return await message.answer(
            "Команда принимает только 2 аргумента.\n"
            "\t/ask_pair [hr] [респондент]  # Порядок важен!"
        )
    try:
        hr, respondent = (
            User.get(User.teleg_username == args[0]),
            User.get(User.teleg_username == args[1]),
        )
        pair = Pair.get(Pair.hr == hr, Pair.respondent == respondent)
    except DoesNotExist:
        return await message.answer(
            "Пара не найдена. Проверьте порядок:\n"
            "\t/ask_pair [hr] [респондент]  # Сначала hr потом респондент"
        )
    await message.answer("Успешно!")
    await get_feedback(pair)


@admin_router.message(Command(commands="admin_reset"))
async def admin_reset(message: types.Message, command: CommandObject):
    if not command.args or len(command.args.split()) <= 0:
        return await message.answer(
            "Не хватает аргументa.\n"
            "\t/admin_reset [admin_username]"
        )
    has_updated = User.update(is_admin=False).where(User.teleg_username << command.args.split())
    await message.answer(f"Успешно обновлено {has_updated} пользователей")


@admin_router.message(Command(commands="change_role"))
async def change_role(message: types.Message, command: CommandObject):
    if not command.args or len(command.args.split()) != 1:
        return await message.answer(
            "Команда принимает только 1 аргумент.\n"
            "\t/change_role [username]"
        )
    user = User.get(User.teleg_username == command.args)
    user.is_hr = not user.is_hr
    user.save()
    await message.answer("Успешно!")


@admin_router.errors(ExceptionTypeFilter(DoesNotExist))
async def user_not_exist(error: types.error_event.ErrorEvent):
    print(vars(error.exception))
    await error.update.message.answer("Пользователь не найден")
