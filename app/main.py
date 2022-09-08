from importlib.machinery import FrozenImporter
import logging
import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src import register_middlewares, admin_router, match_router, auth_router
from db.models import create_tables
from config import BOT


logger_file_handler = logging.FileHandler('bot.log')
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setLevel(logging.INFO)
logger_stream_handler.setFormatter(logging.Formatter(
    '[%(levelname)s %(asctime)s]\n%(message)s', datefmt='"%d/%m %H.%M"',
))
logger_file_handler.setLevel(logging.DEBUG)
logging.basicConfig(
    datefmt='"%d/%m %H.%M"',
    format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
    level=logging.DEBUG,
    handlers=(logger_file_handler, logger_stream_handler)
)
logger = logging.getLogger()


async def main():
    logger.info('RUN APP')
    create_tables()
    logger.info('Created tables')
    dp = Dispatcher(MemoryStorage())
    register_middlewares(dp)
    dp.include_router(auth_router)
    dp.include_router(admin_router)
    dp.include_router(match_router)

    try:
        return await dp.start_polling(BOT)
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover
        logger.info('Bot stopped')


if __name__ == '__main__':
    asyncio.run(main())
