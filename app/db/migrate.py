from peewee import PostgresqlDatabase
from playhouse import migrate

from .models import User


def teleg_username_to_nullable(database: PostgresqlDatabase):
    migrator = migrate.PostgresqlMigrator(database)
    return migrate.migrate(
        migrator.drop_not_null(User._meta.table_name)
    )

