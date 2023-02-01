import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from app.src import register_middlewares, register_routers
from app.db import init_db
from app.config import get_config


logger_file_handler = logging.FileHandler("bot.log")
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setLevel(logging.INFO)
logger_stream_handler.setFormatter(
    logging.Formatter(
        "[%(levelname)s %(asctime)s]\n%(message)s",
        datefmt='"%d/%m %H.%M"',
    )
)
logger_file_handler.setLevel(logging.DEBUG)
logging.basicConfig(
    datefmt='"%d/%m %H.%M"',
    format="%(levelname)s:%(name)s:%(asctime)s:%(message)s",
    level=logging.DEBUG,
    handlers=(logger_file_handler, logger_stream_handler),
)
logger = logging.getLogger()


async def main():
    logger.info("RUN APP")
    config = get_config()
    bot = Bot(config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    await init_db(config)
    logger.info("Created tables")

    register_middlewares(dp)
    register_routers(dp)

    try:
        return await dp.start_polling(bot, config=config)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
