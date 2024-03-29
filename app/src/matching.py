import asyncio
import datetime

from aiogram import Bot, Router, types, F

from app.db.models import User, Pair
from app.db import database
from app.logger import logger


match_router = Router()


@match_router.callback_query(F.data == "deactivate_user")
async def deactivate_user(data: types.CallbackQuery | types.Message, model_user: User):
    model_user.is_active = False
    model_user.save()
    await data.message.edit_text(
        "Вас исключили из списка для подбора пар.\n"
        "Вы можете это исправить в меню (вызвать меню можно командой /start)"
    )


async def get_profile_text(user: User):
    hr_link = (
        "https://praktikum.notion.site/random\\-coffee\\-IT\\-5df78a17680a429f80d110dcfdb491d2"
    )
    user_link = (
        "https://praktikum.notion.site/random\\-coffee\\-IT\\-0dbc947e5ed34871a7b07e750c571a23"
    )
    return (
        "Твоя пара на эту неделю:\n"
        f"Имя: {user.full_name}\n"
        f"Профессия: {user.profession}\n"
        f"Телерграм: {user.mention}\n"
        "Напиши своей паре приветствие и предложи удобные дни и время для созвона."
        "В разговоре вы можете опираться на этот <a href=" + (
            f'"{hr_link}"' if user.is_hr else f'"{user_link}"'
        ) + ">гайд</a>"
    )


@match_router.callback_query(F.data == "start_matching")
async def start_matching(
    data: types.CallbackQuery | types.Message, model_user: User, bot: Bot
):
    answer = data.message.edit_text
    non_complete_date = (
        model_user.pairs.where(Pair.complete == False)
    )

    if non_complete_date:
        pair: Pair = non_complete_date[0]
        to_user: User = pair.respondent if model_user.is_hr else pair.hr
        return await answer(
            f"У вас уже есть не законченная встреча c {to_user.mention}!",
            parse_mode="HTML",
        )

    model_user.is_active = True
    model_user.save()
    await data.answer("Ищу пару...")
    to_user = await get_match(model_user)

    if not to_user:
        model_user.last_matching_date = datetime.datetime.now()
        return await answer(
            "К сожалению прямо сейчас сейчас я не смог подобрать вам пару, "
            "но как только у меня появится кандидат, сразу вам напишу."
        )
    logger.info("New pair %s -> %s", model_user, to_user)
    # To current user
    await answer(text=await get_profile_text(to_user), parse_mode="HTML")
    # To match user
    await bot.send_message(
        to_user.teleg_id, await get_profile_text(model_user), parse_mode="HTML"
    )


@database.atomic()
def _create_pair(user, to_user) -> Pair:
    if user.is_hr:
        pair = Pair.create(
            hr=user, respondent=to_user
        )
    else:
        pair = Pair.create(
            hr=to_user, respondent=user
        )
    user.is_active = to_user.is_active = False
    user.save()
    to_user.save()
    return pair


def _get_pair(user):
    active_users = (
        User.select()
        .where(User.is_active == True, User.is_hr == (not user.is_hr))
        .order_by(User.last_matching_date)
    )
    for to_user in active_users:
        _pair = user.pairs.where((Pair.respondent if user.is_hr else Pair.hr) == to_user)
        if _pair.exists():
            continue
        return to_user


async def get_match(user: User) -> User:
    if not user.is_active:
        logger.error(
            "Unable to find a pair for an inactivate user: %s", user.teleg_username
        )
        return
    to_user = _get_pair(user)

    if not to_user:
        logger.info("Pair not defined for the user %s", user.teleg_username)
        return

    new_pair = _create_pair(user, to_user)
    logger.info("New pair: %s", new_pair)
    return to_user


async def get_feedback(pair: Pair):
    logger.info("pair completed! (%s)", pair)
    pair.date_complete = datetime.datetime.now()
    pair.complete = True
    pair.save()
    hr_buttons = [
        [
            types.InlineKeyboardButton(
                text="Да!", callback_data=f"match_complite_{pair.id}"
            ),
            types.InlineKeyboardButton(
                text="Нет", callback_data=f"match_not_complite_{pair.id}"
            ),
        ]
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=hr_buttons)
    await pair_send_message(
        pair,
        {"text": "Удалось ли созвониться?", "reply_markup": keyboard},
        {
            "text": (
                "Спасибо большое за участие! Если вам хочется "
                "поучаствовать снова, просто нажми на кнопку GO"
            ),
            "reply_markup": types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="GO", callback_data="start_matching"
                        )
                    ]
                ]
            ),
        },
    )


@match_router.callback_query(F.data[:19] == "match_not_complite_")
async def match_not_complite(data: types.CallbackQuery, bot: Bot):
    await data.message.delete()
    pair_id = int(data.data[19:])
    pair = Pair.get(Pair.id == pair_id)
    buttons = [[types.InlineKeyboardButton(text="GO", callback_data="start_matching")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(
        pair.hr.teleg_id,
        text=(
            "Пожалуйста, напиши в телеграм @arr_ink, она поможет :)\n"
            'Если хочешь найти другую пару нажми "GO"'
        ),
        reply_markup=keyboard,
    )


@match_router.callback_query(F.data[:15] == "match_complite_")
async def match_complite(data: types.CallbackQuery, bot: Bot):
    await data.message.delete()
    pair_id = int(data.data[15:])
    pair = Pair.get(Pair.id == pair_id)
    buttons = [[types.InlineKeyboardButton(text="GO", callback_data="start_matching")]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(
        pair.hr.teleg_id,
        text=(
            "Поделись своими эмоциями в канале communication! "
            "Если вы захотите участвовать еще раз, просто нажми на кнопку GO"
        ),
        reply_markup=keyboard,
    )


async def pair_send_message(
    pair: Pair,
    message_to_hr: dict,
    bot: Bot,
    message_to_respondent: dict | None = None,
):
    if not message_to_respondent:
        message_to_respondent = message_to_hr
    await asyncio.gather(
        bot.send_message(pair.hr.teleg_id, **message_to_hr),
        bot.send_message(pair.respondent.teleg_id, **message_to_respondent),
    )


async def ask_pairs():
    logger.info("Asking pairs...")
    non_complite_pairs = Pair.select().where(
        Pair.complete == False,
        Pair.match_date <= datetime.datetime.now() - datetime.timedelta(days=5),
    )
    for non_complite_pair in non_complite_pairs:
        await get_feedback(non_complite_pair)

    logger.info("Asking complite!")
