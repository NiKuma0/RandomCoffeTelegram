import threading
import os

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage


TESTING = True
# DB settings
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB')
# Bot settings
THREADING_EVENT = threading.Event() # For schedule
BOT_TOKEN = os.getenv('BOT_TOKEN') or '5199481941:AAG2Pc1eeX68owu5tqT-yheRty7j0M7ONrY'
DP = Dispatcher(MemoryStorage())
BOT = Bot(BOT_TOKEN, parse_mode='HTML')
