import logging
import asyncio

from src import register_middlewares, admin_router, match_router, auth_router, run_continuously
from db.models import create_tables
from config import BOT, DP


logger_file_handler = logging.FileHandler('bot.log')
logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setLevel(logging.INFO)
logger_stream_handler.setFormatter(logging.Formatter('[%(levelname)s]\n%(message)s'))
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
    register_middlewares()
    DP.include_router(auth_router)
    DP.include_router(admin_router)
    DP.include_router(match_router)
    run_continuously()


if __name__ == '__main__':
    asyncio.run(main())
    DP.run_polling(BOT)
