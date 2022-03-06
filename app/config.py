import threading
import os

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage


TESTING = True
# DB settings
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB') or 'app'
# Bot settings
THREADING_EVENT = threading.Event() # For schedule
BOT_TOKEN = os.getenv('BOT_TOKEN')
DP = Dispatcher(MemoryStorage())
BOT = Bot(BOT_TOKEN, parse_mode='HTML')
