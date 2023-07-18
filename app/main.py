import asyncio

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from app.src import register_middlewares, register_routers
from app.db import init_db, database
from app.config import get_config, Config
from app.logger import logger


def init_bot(config: Config) -> tuple[Dispatcher, Bot]:
    bot = Bot(config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    @dp.startup()
    async def _(dispatcher: Dispatcher, config: Config):
        await init_db(config=config)
        register_middlewares(dispatcher)
        register_routers(dispatcher)
        logger.info('Bot start')

    @dp.shutdown()
    async def _():
        database.close()
        logger.info('Bot Stopped')

    return dp, bot


def main():
    config = get_config()
    dp, bot = init_bot(config)
    return asyncio.run(dp.start_polling(bot, config=config))
