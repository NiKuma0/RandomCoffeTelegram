import os

from aiogram import Bot


TESTING = False
# DB settings
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT = Bot(BOT_TOKEN, parse_mode="HTML")
ADMINS = os.getenv("ADMINS")
