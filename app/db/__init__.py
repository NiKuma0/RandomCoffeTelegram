import peewee
import peewee_async

from config import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER

database = peewee_async.PostgresqlDatabase(
    POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host="db", port=5432
)


class Manager(peewee_async.Manager):
    database = database


class BaseModel(peewee.Model):
    class Meta:
        database = database
