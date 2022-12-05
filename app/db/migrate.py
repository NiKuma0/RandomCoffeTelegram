from peewee import PostgresqlDatabase
from playhouse import migrate

from .models import User

from . import database


def drop_not_null_teleg_username(database: PostgresqlDatabase = database) -> None:
    migrator = migrate.PostgresqlMigrator(database)
    migrate.migrate(
        migrator.drop_not_null(User._meta.table_name, 'teleg_username')
    )
