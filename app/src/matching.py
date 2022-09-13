import asyncio
import logging
import datetime

from aiogram import Router, types, F

from db.models import User, Pair
from db import Manager
from config import BOT


logger = logging.getLogger(__name__)
bot = BOT
match_router = Router()


@match_router.callback_query(F.data == 'deactivate_user')
async def deactivate_user(data: types.CallbackQuery | types.Message, model_user: User):
    model_user.is_active = False
    model_user.save()
    await data.message.edit_text(
        'Вас исключили из списка для подбора пар.\n'
        'Вы можете это исправить в меню (вызвать меню можно командой /start)'
    )


@match_router.callback_query(F.data == 'start_matching')
async def start_matching(data: types.CallbackQuery | types.Message, model_user: User):
    answer = data.message.edit_text
    manager = Manager()
    if datetime.datetime.now() - model_user.register_date >= datetime.timedelta(weeks=14):
        model_user.is_active = False
        model_user.save()
        Pair.delete().where(
            Pair.hr == model_user
            if model_user.is_hr else
            Pair.respondent == model_user
        ).execute()
        logger.info(f'@{model_user.teleg_username} has blocked')
        return await answer(
            'Ваш профиль заблокирован т.к. срок жизни аккаунта 3 месяца.'
        )
    non_complite_date = await manager.execute(model_user.pairs.where(
        Pair.complete == False
    ))
    
    if non_complite_date:
        pair: Pair = non_complite_date[0]
        to_user = pair.respondent if model_user.is_hr else pair.hr
        return await answer(
            f'У вас уже есть не законченная встреча c {to_user.mention}!',
            parse_mode='HTML'
        )

    model_user.is_active = True
    await manager.update(model_user)
    await data.answer('Ищу пару...')
    to_user = await get_match(model_user)

    if not to_user:
        model_user.last_matching_date = datetime.datetime.now()
        return await answer(
            'К сожалению прямо сейчас сейчас я не смог подобрать вам пару, '
            'но как только у меня появится кандидат, сразу вам напишу.'
        )
    text = lambda user: (
        'Твоя пара на эту неделю:\n'
        f'Имя: {user.full_name}\n'
        f'Профессия: {user.profession}\n'
        f'Телерграм: {user.mention}\n'
        'Напиши своей паре приветствие и предложи удобные дни и время для созвона.'
        'В разговоре вы можете опираться на этот <a href='
        + (
        '"https://praktikum.notion.site/random\\-coffee\\-IT\\-5df78a17680a429f80d110dcfdb491d2"'
        if user.is_hr else 
        '"https://praktikum.notion.site/random\\-coffee\\-IT\\-0dbc947e5ed34871a7b07e750c571a23"'
        ) + '>гайд</a>'
    )
    logger.info(f'New pair {model_user} -> {to_user}')
    # To current user
    await answer(
        text=text(to_user),
        parse_mode='HTML'
    )
    # To match user
    await BOT.send_message(
        to_user.teleg_id,
        text(model_user),
        parse_mode='HTML'
    )


async def get_match(user: User) -> User:
    if not user.is_active:
        logger.error(f'Unable to find a pair for an inactivate user: {user.teleg_username}')
        return
    manager = Manager()
    active_users = await manager.execute(
        User.select()
        .where(
            User.is_active == True,
            User.is_hr == (not user.is_hr)
        ).order_by(User.last_matching_date)
    )
    user_pair_field, to_user_pair_field = (Pair.hr, Pair.respondent) if user.is_hr else (Pair.respondent, Pair.hr)
    query = user.pairs
    to_user: User = None
    for choice in active_users:
        _pairs = await manager.execute(query.where(to_user_pair_field == choice))
        if _pairs:
            continue
        to_user = choice
    if not to_user:
        logger.info(f'Pair not defined for the user {user.teleg_username}')
        return
    logger.info(f'New pair: {user.teleg_username} -> {to_user.teleg_username}')
    await manager.create(Pair, **{
        user_pair_field.column_name: user,
        to_user_pair_field.column_name: to_user
    }) 
    user.is_active = False
    to_user.is_active = False
    await manager.update(user)
    await manager.update(to_user)
    return to_user


async def get_feedback(pair: Pair):
    logger.info(f'pair completed! ({pair})')
    manager = Manager()
    pair.date_complete = datetime.datetime.now()
    pair.complete = True
    await manager.update(pair)
    hr_buttons = [[
        types.InlineKeyboardButton(text='Да!', callback_data=f'match_complite_{pair.id}'),
        types.InlineKeyboardButton(text='Нет', callback_data=f'match_not_complite_{pair.id}')
    ]]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=hr_buttons)
    await pair_send_message(
        pair,
        {'text': 'Удалось ли созвониться?',
        'reply_markup': keyboard},
        {'text': ('Спасибо большое за участие! Если вам хочется '
        'поучаствовать снова, просто нажми на кнопку GO'),
        'reply_markup': types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text='GO', callback_data='start_matching')]]
        )}
    )


@match_router.callback_query(F.data[:19] == 'match_not_complite_')
async def match_not_complite(data: types.CallbackQuery):
    await data.message.delete()
    pair_id = int(data.data[19:])
    manager = Manager()
    pair = await manager.get(Pair, Pair.id == pair_id)
    buttons = [[
        types.InlineKeyboardButton(text='GO', callback_data='start_matching')
    ]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await BOT.send_message(
        pair.hr.teleg_id,
        text=('Пожалуйста, напиши в телеграм @ksu_bark, она поможет :)\n'
        'Если хочешь найти другую пару нажми "GO"'),
        reply_markup=keyboard
    )


@match_router.callback_query(F.data[:15] == 'match_complite_')
async def match_complite(data: types.CallbackQuery, model_user: User):
    await data.message.delete()
    pair_id = int(data.data[15:])
    manager = Manager()
    pair = await manager.get(Pair, Pair.id == pair_id)
    buttons = [[
        types.InlineKeyboardButton(text='GO', callback_data='start_matching')
    ]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await BOT.send_message(
        pair.hr.teleg_id,
        text=('Поделись своими эмоциями в канале communication! '
        'Если вы захотите участвовать еще раз, просто нажми на кнопку GO'),
        reply_markup=keyboard
    )


async def pair_send_message(pair: Pair, message_to_hr: dict, message_to_respondent: dict=None):
    if not message_to_respondent:
        message_to_respondent = message_to_hr
    await asyncio.gather(
        BOT.send_message(pair.hr.teleg_id, **message_to_hr),
        BOT.send_message(pair.respondent.teleg_id, **message_to_respondent)
    )


async def ask_pairs():
    logger.info('Asking pairs...')
    manager = Manager()
    non_complite_pairs = await manager.execute(
        Pair.select()
        .where(
            Pair.complete == False,
            Pair.match_date <= datetime.datetime.now() - datetime.timedelta(days=5)
        )
    )
    [await get_feedback(non_complite_pair) for non_complite_pair in non_complite_pairs]
    logger.info('Asking complite!')
