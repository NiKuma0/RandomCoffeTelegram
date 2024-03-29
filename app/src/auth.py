from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app.db.models import User, Profession
from app.config import Config
from app.filters import Order
from app.logger import logger


HR_PASSWORD = "hr_hire"
STUDENT_PASSWORD = "student_hire"
auth_router = Router()


@auth_router.message(Command(commands="start"))
async def start(
    message: types.Message, state: FSMContext, model_user: User | None, answer
):
    if model_user is None:
        logger.info("New user join to us %s", message.from_user.username)
        await state.set_state(Order.waiting_for_password)
        return await message.answer("Введите ваш код:")
    await send_profile(model_user, state, answer)


@auth_router.message(Command(commands="help"))
async def help_message(message: types.Message, model_user: User):
    base_text = (
        "Основные команды:\n"
        "/start - Открывает меню. Здесь можно прекратить поиск пар или возобновить его, "
        "а также изменить свой профиль.\n"
    )
    admin_text = (
        "Команды для администратора:\n"
        "/add_admin - Добавляет администратора.\n"
        "Пример:\n"
        "   /add_admin @user1 @user2 @user3\n"
        "/add_profession - Добавляет профессию для студентов-респондентов\n"
        "Пример:\n"
        "   /add_profession Python Developer\n"
        '/ask_pairs - Команда нужна для "ручного" запуска проверки пар\n'
        "/ask_pair - Бот игнорирует время когда была создана пара, и спрашивает "
        'у неё - "как прошла встреча?"\n'
    )
    text = base_text + (admin_text if model_user.is_admin else "")
    await message.answer(text)


@auth_router.message(Order.waiting_for_password)
async def check_password(
    message: types.Message,
    event_from_user: types.User,
    state: FSMContext,
    answer,
    config: Config,
):
    if message.text not in (HR_PASSWORD, STUDENT_PASSWORD):
        return await message.answer("Неверный пароль. Попробуйте снова")

    model_user = User.create(
        teleg_id=event_from_user.id,
        teleg_username=event_from_user.username or event_from_user.full_name,
        is_hr=message.text == HR_PASSWORD,
        is_admin=event_from_user.id == config.ADMINS,
        first_name=event_from_user.first_name,
        last_name=event_from_user.last_name,
    )
    logger.info(
        "New user (%s, %s) in Data Base", model_user.teleg_username, model_user.teleg_id
    )
    text = (
        "Этот бот нужен для проведения random coffee. Наш бот предлагает вам "
        "поучаствовать в неформальном разговоре с выпускником Практикума по IT-направлению. "
        'Для этого необходимо нажать на кнопку "Поехали". Нажмите как только будете готовы.'
        if model_user.is_hr
        else "Этот бот нужен для проведения random coffee. Наш бот предлагает вам "
        "поучаствовать в неформальном разговоре с начинающим it-рекрутером Практикума. "
        'Для этого необходимо нажать на кнопку "Поехали". Нажмите как только будете готовы.'
    )
    await state.set_state(Order.about_bot)
    await answer(
        text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text="Поехали", callback_data="set_profile"
            )
        ]]),
    )


@auth_router.callback_query(F.data == "set_profile")
async def ack_about_change_name(_data, model_user: User, state: FSMContext, answer):
    buttons = [[
        types.InlineKeyboardButton(text="Да", callback_data="yes"),
        types.InlineKeyboardButton(text="Нет", callback_data="not"),
    ]]
    await state.set_state(Order.waiting_for_real_name)
    await answer(
        f"Это ваше настоящее имя: {model_user.full_name}?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@auth_router.callback_query(Order.waiting_for_real_name)
async def answer_about_change_name(
    data: types.CallbackQuery, state: FSMContext, model_user: User, answer
):
    if data.data == "not":
        return await data.message.edit_text("Напишите своё настоящее имя")
    if data.data != "yes":
        return logger.error("Unknown data: %s", data.data)
    await change_name(data, state, model_user, answer)


@auth_router.message(Order.waiting_for_real_name)
async def change_name(message, state: FSMContext, model_user: User, answer):
    if isinstance(message, types.Message):
        if len(message.text) > User.full_name_max_length():
            return message.answer(
                f"В имени не может быть больше {model_user.full_name_max_length} символов."
            )
        model_user.full_name = message.text
        model_user.save()
    if model_user.is_admin or model_user.is_hr:
        return await send_profile(model_user, state, answer)
    await state.set_state(Order.set_profession)
    await get_professions(message, check_data=False)


@auth_router.callback_query(F.data[:5] == "page_")
async def get_professions(data: types.CallbackQuery | types.Message, check_data=True):
    page = None
    if check_data:
        page = int(data.data[5:])
    keyboard = await profession_paginator(page)
    if isinstance(data, types.CallbackQuery):
        return await data.message.edit_text("Укажите профессию:", reply_markup=keyboard)
    return await data.answer("Укажите профессию:", reply_markup=keyboard)


@auth_router.callback_query(F.data[:11] == "profession_", Order.set_profession)
async def set_profession(data: types.CallbackQuery, model_user: User, state, answer):
    profession_pk = int(data.data[11:])
    model_user.profession = profession_pk
    model_user.save()
    await send_profile(model_user, state, answer)


async def profession_paginator(page=None) -> types.InlineKeyboardMarkup:
    page = page or 1
    count_items = 3
    switch = []
    query = Profession.select().order_by(Profession.id)

    buttons = [
        [types.InlineKeyboardButton(
            text=profession.name, callback_data=f"profession_{profession.id}"
        )]
        for profession in query.paginate(page, count_items)
    ]

    if page != 1:
        switch.append(
            types.InlineKeyboardButton(text="<", callback_data=f"page_{page - 1}")
        )
    if page * count_items < query.count():
        switch.append(
            types.InlineKeyboardButton(text=">", callback_data=f"page_{page + 1}")
        )
    if switch:
        buttons.append(switch)
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_profile(model_user: User, state: FSMContext, answer):
    """
    Send profile and clear state
    """
    await state.clear()
    buttons = [
        [
            types.InlineKeyboardButton(
                text="Не хочу пока участвовать", callback_data="deactivate_user"
            )
        ]
        if model_user.is_active
        else [types.InlineKeyboardButton(text="GO", callback_data="start_matching")],
        [
            types.InlineKeyboardButton(
                text="Изменить профиль", callback_data="set_profile"
            )
        ],
    ]
    await answer(
        "Вызвать это меню можно командой /start\n"
        "Ваш профиль:\n"
        f"Имя: {model_user.full_name}\n"
        f"Профессия: {model_user.profession}\n"
        f"Телеграм: {model_user.mention}\n" + (
            "Если пока не хотите участвовать нажмите на кнопку ниже"
            if model_user.is_active
            else 'Если вы готовы начать нажмите "GO"'
        ),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
