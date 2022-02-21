import peewee

from config import TESTING, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER

if TESTING:
    database = peewee.SqliteDatabase('bot.db')
else:
    database = peewee.PostgresqlDatabase(
        POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD,
        host='db', port=5432
    )

class BaseModel(peewee.Model):
    class Meta:
        database = database
