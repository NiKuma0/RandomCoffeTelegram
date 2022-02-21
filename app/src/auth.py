import logging
from subprocess import call

from aiogram import types, Router, F
from aiogram.dispatcher.fsm.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext

from db.models import User, Profession


HR_PASSWORD = 'hr_hire'
STUDENT_PASSWORD = 'student_hire'
logger = logging.getLogger(__name__)
auth_router = Router()


class Order(StatesGroup):
    waiting_for_password = State()
    waiting_for_real_name = State()
    set_profession = State()
    start = State()


@auth_router.message(commands='start')
async def start(message: types.Message, state: FSMContext, model_user: User | None):
    if model_user is None:
        await message.answer('Введите ваш код:')
        logger.info(f'New user join to us {message.from_user.username}')
        return await state.set_state(Order.waiting_for_password)
    await state.clear()
    buttons = [
        [types.InlineKeyboardButton(text='Запустить подбор пар', callback_data='start_matching')],
        [types.InlineKeyboardButton(text='Перезаполнить профиль', callback_data='set_profile')],
        [types.InlineKeyboardButton(text='Не хочу пока участвовать', callback_data='deactivate_user')]
    ]
    await message.answer(
        'Это меню. Здесь ты можешь изменить свой профиль, попробовать запусть подбор пар или исключить себя из списка подбора пар.',
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@auth_router.message(state=Order.waiting_for_password)
async def check_password(message: types.Message, event_from_user: types.User, state: FSMContext):
    if message.text not in (HR_PASSWORD, STUDENT_PASSWORD):
        return await message.answer('Неверный пароль. Попробуйте снова')
    model_user = User.create(
        teleg_id=event_from_user.id,
        teleg_username=event_from_user.username,
        is_hr=message.text == HR_PASSWORD,
        first_name=event_from_user.first_name,
        last_name=event_from_user.last_name
    )
    logger.info(f'New user ({model_user.teleg_username}, {model_user.teleg_id}) in Data Base')
    text = (
        'Этот бот нужен для проведения random coffe. Наш бот предлагает тебе '
        'поучаствовать в неформальном разговоре с выпускником Практикума по IT-направлению. '
        'Для этого необходимо нажать на кнопку "Поехали". Если на этой неделе вы не '
        'готовы участовать в random coffe, просто нажмите "В следующий раз".'
        if model_user.is_hr else
        'Этот бот нужен для проведения random coffe. Наш бот предлагает тебе '
        'поучаствовать в неформальном разговоре с начинающим it-рекрутером Практикума. '
        'Для этого необходимо нажать на кнопку "Поехали". Если на этой неделе вы не '
        'готовы участовать в random coffe, просто нажмите "В следующий раз".'
    )
    await message.answer(
        text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Поехали', callback_data='set_profile')]
        ])
    )


@auth_router.callback_query(F.data == 'set_profile')
async def ack_about_change_name(data: types.CallbackQuery|types.Message, model_user: User, state: FSMContext):
    buttons = [[
        types.InlineKeyboardButton(text='Да', callback_data='yes'),
        types.InlineKeyboardButton(text='Нет', callback_data='not')
    ]]
    if isinstance(data, types.CallbackQuery):
        answer = data.message.edit_text
    elif isinstance(data, types.Message):
        answer = data.answer
    else:
        raise f'Don`t supporeted type of data {type(data).__name__}'
    await state.set_state(Order.waiting_for_real_name)
    await answer(
        f'Это ваше настоящее имя: {model_user.full_name}?',
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@auth_router.callback_query(state=Order.waiting_for_real_name)
async def answer_about_change_name(data: types.CallbackQuery, state: FSMContext, model_user: User):
    if data.data == 'not':
        return await data.message.edit_text('Напишете своё настоящее имя')
    elif data.data != 'yes':
        return logger.error(f'Unknown data: {data.data}')
    await change_name(data, state, model_user)


@auth_router.message(state=Order.waiting_for_real_name)
async def change_name(message: types.Message | types.CallbackQuery, state: FSMContext, model_user: User):
    if isinstance(message, types.Message):
        model_user.full_name = message.text
        model_user.save()
    if not (model_user.is_admin or model_user.is_hr):
        await state.set_state(Order.set_profession)
        return await get_professions(message, check_data=False)
    await send_profile(model_user, message, state)
 

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
async def set_profession(data: types.CallbackQuery, model_user: User, state):
    profession_pk = int(data.data[11:])
    model_user.profession = profession_pk
    model_user.save()
    await send_profile(model_user, data, state)


async def profession_paginator(page=None) -> types.InlineKeyboardMarkup:
    page = page or 1
    count_items = 3
    professions = Profession.select().order_by(Profession.id)
    switch = []
    buttons = [
        [types.InlineKeyboardButton(text=profession.name, callback_data=f'profession_{profession.id}')]
        for profession in professions.paginate(page, count_items)
    ]
    if page != 1:
        switch.append(
            types.InlineKeyboardButton(text='<', callback_data=f'page_{page - 1}')
        )
    if page * count_items < professions.count():
        switch.append(
            types.InlineKeyboardButton(text='>', callback_data=f'page_{page + 1}')
        )
    buttons.append(switch) if switch else None
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_profile(model_user: User, data: types.Message | types.CallbackQuery, state: FSMContext):
    '''
    Send profile and clear state
    '''
    await state.clear()
    text = (
        'Твой профиль:\n'
        f'Имя: {model_user.full_name}\n'
        f'Профессия: {model_user.profession}\n'
        f'Телеграм: @{model_user.teleg_username}\n'
        'Готовы начать?'
    )
    buttons = [[
        types.InlineKeyboardButton(text='Да, Начнём!', callback_data='start_matching'),
    ]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(data, types.CallbackQuery):
        return await data.message.edit_text(text, reply_markup=keyboard)
    if isinstance(data, types.Message):
        return await data.answer(text, reply_markup=keyboard)
    return logger.error(f'Don`t supported type of data: "{type(data).__name__}"') 
