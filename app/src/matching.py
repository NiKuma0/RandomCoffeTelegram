import asyncio
import logging
import threading
import datetime
import time

import schedule
from aiogram import Router, types, F

from db.models import User, Pair
from config import THREADING_EVENT, BOT


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
    non_complite_date = model_user.pairs.where(
        Pair.complete == False
    )
    
    if non_complite_date.exists():
        pair: Pair= non_complite_date.first()
        to_user = pair.respondent if model_user.is_hr else pair.hr
        return await answer(
            f'У вас уже есть не законченная встреча c @{to_user.teleg_username}!'
        )
    model_user.is_active = True
    model_user.save()
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
        f'Телерграм: @{user.teleg_username}\n'
        'Напиши своей паре приветсвие и предложи удобные дни и время для созвона.'
        'В разговоре вы можете опираться на этот гайд '
        + (
        '(https://praktikum.notion.site/random-coffee-IT-5df78a17680a429f80d110dcfdb491d2)'
        if user.is_hr else 
        '(https://praktikum.notion.site/random-coffee-IT-0dbc947e5ed34871a7b07e750c571a23)'
        )
    )
    logger.info(f'New pair {model_user} -> {to_user}')
    await answer(text=text(to_user))
    await BOT.send_message(
        to_user.teleg_id,
        text(model_user)
    )


async def get_match(user: User) -> User:
    if not user.is_active:
        logger.error(f'Unable to find a pair for an inactivate user: {user.teleg_username}')
        return
    active_users = (
        User.select()
        .where(
            User.is_active == True,
            User.is_hr == (not user.is_hr)
        ).order_by(User.last_matching_date)
    )
    user_pair_field, to_user_pair_field = (Pair.hr, Pair.respondent) if user.is_hr else (Pair.respondent, Pair.hr)
    pairs = user.pairs.select()
    to_user: User= None
    for choice in active_users:
        if pairs.where(to_user_pair_field == choice).exists():
            continue
        to_user = choice
    if not to_user:
        logger.info(f'Pair not defined for the user {user.teleg_username}')
        return
    logger.info(f'New pair: {user.teleg_username} -> {to_user.teleg_username}')
    Pair.create(**{
        user_pair_field.column_name: user,
        to_user_pair_field.column_name: to_user
    }) 
    user.is_active = False
    to_user.is_active = False
    user.save()
    to_user.save()
    return to_user


async def get_feedback(pair: Pair):
    pair.date_complete = datetime.datetime.now()
    pair.complete = True
    pair.save()
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
    pair = Pair.get_by_id(pair_id)
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
    pair: Pair = Pair.get_by_id(pair_id)
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


async def overdue(pair: Pair):
    buttons = [[types.InlineKeyboardButton(text='Да', callback_data='start_matching')]]
    text = {
        'text': 'Ваша пара просрочена (срок жизни пары 10 дней). Хотите найти другую?',
        'reply_markup': types.InlineKeyboardMarkup(inline_keyboard=buttons) 
    }
    await pair_send_message(pair, text)

def ask_pairs():
    overdue_pair = (
        Pair.select()
        .where(
            Pair.complete == False,
            Pair.match_date <= datetime.datetime.now() - datetime.timedelta(days=10)
        )
    )
    asyncio.gather(*map(overdue, overdue_pair))
    Pair.update(complete=True).where(
        Pair.complete == False,
        Pair.match_date <= datetime.datetime.now() - datetime.timedelta(days=10)
    ).execute()
    non_compiled_pairs = (
        Pair.select()
        .where(
            Pair.complete == False,
            Pair.match_date >= datetime.datetime.now() - datetime.timedelta(days=5)
        )
    )
    asyncio.gather(*map(get_feedback, non_compiled_pairs))


schedule.every().day.do(ask_pairs)

def run_continuously(interval=1):
    cease_continuous_run = THREADING_EVENT
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run
