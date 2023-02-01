import peewee
import peewee_async

from app.config import Config


database = peewee.DatabaseProxy()


class Manager(peewee_async.Manager):
    database = database


class BaseModel(peewee.Model):
    class Meta:
        database = database


async def init_db(*, config: Config):
    from .models import create_tables

    database.initialize(
        peewee_async.PostgresqlDatabase(
            config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host="localhost",
            port=5432,
        )
    )
    create_tables()
