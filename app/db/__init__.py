import os

import peewee
import peewee_async
from psycopg2 import extensions
from gevent.socket import wait_read, wait_write

from app.config import Config


database: peewee.PostgresqlDatabase = peewee.DatabaseProxy()


class Manager(peewee_async.Manager):
    database = database


class BaseModel(peewee.Model):
    class Meta:
        database = database


def _psycopg2_gevent_callback(conn, timeout=None):
    while True:
        state = conn.poll()
        if state == extensions.POLL_OK:
            break
        if state == extensions.POLL_READ:
            wait_read(conn.fileno(), timeout=timeout)
        elif state == extensions.POLL_WRITE:
            wait_write(conn.fileno(), timeout=timeout)
        else:
            raise ValueError('poll() returned unexpected result')


async def init_db(*, config: Config):
    database.initialize(
        peewee.PostgresqlDatabase(
            config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host="localhost",
            port=5432,
        )
    )
    extensions.set_wait_callback(_psycopg2_gevent_callback)


def migrate():
    with open(os.path.join(os.path.dirname(__file__), "migrate.sql"), "r", encoding="UTF-8") as sql:
        database.execute_sql(sql.read())
