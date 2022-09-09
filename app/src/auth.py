import logging

from aiogram import types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMINS

from db.models import User, Profession
from db import Manager


HR_PASSWORD = 'hr_hire'
STUDENT_PASSWORD = 'student_hire'
logger = logging.getLogger(__name__)
auth_router = Router()


class Order(StatesGroup):
    waiting_for_password = State()
    about_bot = State()
    waiting_for_real_name = State()
    set_profession = State()
    start = State()


@auth_router.message(commands='start')
async def start(message: types.Message, state: FSMContext, model_user: User | None, answer):
    if model_user is None:
        await message.answer('Введите ваш код:')
        logger.info(f'New user join to us {message.from_user.username}')
        return await state.set_state(Order.waiting_for_password)
    await send_profile(model_user, state, answer)


@auth_router.message(commands='help')
async def help_message(message: types.Message, model_user: User):
    base_text = (
        'Основные команды:\n'
        '/start - Открывает меню. Здесь можно прекратить поиск пар или возобновить его, '
        'а также изменить свой профиль.\n'
    )
    admin_text = (
        'Команды для администратора:\n'
        '/add_admin - Добавляет администратора.\n'
        'Пример:\n'
        '   /add_admin @user1 @user2 @user3\n'
        '/add_profession - Добавляет профессию для студентов-респондентов\n'
        'Пример:\n'
        '   /add_profession Python Developer\n'
        '/ask_pairs - Команда нужна для "ручного" запуска проверки пар\n'
        '/ask_pair - Бот игнорирует время когда была создана пара, и спрашивает '
        'у неё - "как прошла встреча?"\n'
    )
    text = base_text + (admin_text if model_user.is_admin else '')
    await message.answer(text)


@auth_router.message(state=Order.waiting_for_password)
async def check_password(message: types.Message, event_from_user: types.User, state: FSMContext, answer):
    if message.text not in (HR_PASSWORD, STUDENT_PASSWORD):
        return await message.answer('Неверный пароль. Попробуйте снова')

    manager = Manager()
    model_user = await manager.create(User,
        teleg_id=event_from_user.id,
        teleg_username=event_from_user.username or event_from_user.full_name,
        is_hr=message.text == HR_PASSWORD,
        is_admin=event_from_user.id == ADMINS,
        first_name=event_from_user.first_name,
        last_name=event_from_user.last_name
    )
    logger.info(f'New user ({model_user.teleg_username}, {model_user.teleg_id}) in Data Base')
    text = (
        'Этот бот нужен для проведения random coffee. Наш бот предлагает вам '
        'поучаствовать в неформальном разговоре с выпускником Практикума по IT-направлению. '
        'Для этого необходимо нажать на кнопку "Поехали". Нажмите как только будете готовы.'
        if model_user.is_hr else
        'Этот бот нужен для проведения random coffee. Наш бот предлагает вам '
        'поучаствовать в неформальном разговоре с начинающим it-рекрутером Практикума. '
        'Для этого необходимо нажать на кнопку "Поехали". Нажмите как только будете готовы.'
    )
    await state.set_state(Order.about_bot)
    await answer(
        text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Поехали', callback_data='set_profile')]
        ])
    )


@auth_router.callback_query(F.data == 'set_profile')
async def ack_about_change_name(data, model_user: User, state: FSMContext, answer):
    buttons = [[
        types.InlineKeyboardButton(text='Да', callback_data='yes'),
        types.InlineKeyboardButton(text='Нет', callback_data='not')
    ]]
    await state.set_state(Order.waiting_for_real_name)
    await answer(
        f'Это ваше настоящее имя: {model_user.full_name}?',
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@auth_router.callback_query(state=Order.waiting_for_real_name)
async def answer_about_change_name(data: types.CallbackQuery, state: FSMContext, model_user: User, answer):
    if data.data == 'not':
        return await data.message.edit_text('Напишете своё настоящее имя')
    elif data.data != 'yes':
        return logger.error(f'Unknown data: {data.data}')
    await change_name(data, state, model_user, answer)


@auth_router.message(state=Order.waiting_for_real_name)
async def change_name(message, state: FSMContext, model_user: User, answer):
    if isinstance(message, types.Message):
        model_user.full_name = message.text
        model_user.save()
    if model_user.is_admin or model_user.is_hr:
        return await send_profile(model_user, state, answer)
    await state.set_state(Order.set_profession)
    await get_professions(message, check_data=False)
 

@auth_router.callback_query(F.data[:5] == 'page_')
async def get_professions(data: types.CallbackQuery | types.Message, check_data=True):
    page = None
    if check_data:
        page = int(data.data[5:])
    keyboard = await profession_paginator(page)
    if isinstance(data, types.CallbackQuery):
        return await data.message.edit_text(
            'Укажите профессию:',
            reply_markup=keyboard
        )
    return await data.answer(
        'Укажите профессию:',
        reply_markup=keyboard
    )


@auth_router.callback_query(F.data[:11] == 'profession_', state=Order.set_profession)
async def set_profession(data: types.CallbackQuery, model_user: User, state, answer):
    profession_pk = int(data.data[11:])
    model_user.profession = profession_pk
    model_user.save()
    await send_profile(model_user, state, answer)


async def profession_paginator(page=None) -> types.InlineKeyboardMarkup:
    page = page or 1
    count_items = 3
    switch = []
    manager = Manager()
    query = Profession.select().order_by(Profession.id)

    buttons = [
        [types.InlineKeyboardButton(text=profession.name, callback_data=f'profession_{profession.id}')]
        for profession in await manager.execute(query.paginate(page, count_items))
    ]

    if page != 1:
        switch.append(
            types.InlineKeyboardButton(text='<', callback_data=f'page_{page - 1}')
        )
    if page * count_items < await manager.count(query):
        switch.append(
            types.InlineKeyboardButton(text='>', callback_data=f'page_{page + 1}')
        )
    buttons.append(switch) if switch else None
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_profile(model_user: User, state: FSMContext, answer):
    '''
    Send profile and clear state
    '''
    await state.clear()
    buttons = [
        [types.InlineKeyboardButton(text='Не хочу пока участвовать', callback_data='deactivate_user')]
        if model_user.is_active else
        [types.InlineKeyboardButton(text='GO', callback_data='start_matching')],
        [types.InlineKeyboardButton(text='Перезаполнить профиль', callback_data='set_profile')],
    ]
    await answer(
        'Вызвать это меню можно командой /start\n'
        'Ваш профиль:\n'
        f'Имя: {model_user.full_name}\n'
        f'Профессия: {model_user.profession}\n'
        f'Телеграм: @{model_user.teleg_username}\n' +
        (
        'Если пока не хотите участвовать нажмите на кнопку ниже'
        if model_user.is_active else
        'Если вы готовы начать нажмите "GO"'
        ),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )
