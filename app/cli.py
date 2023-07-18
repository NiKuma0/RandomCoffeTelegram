import click
import asyncio
import logging

from app.config import get_config
from app.db import migrate as start_migrate
from app.db.models import create_tables as _create_tables
from app.main import init_bot
from app.logger import logger, BotLogger


config = get_config()
dispatcher, bot = init_bot(config)


@click.group()
@click.option(
    "-v", "--verbose",
    default="INFO",
    help="Logging level.",
)
@click.option(
    "--no-log-file",
    is_flag=True,
    default=False,
    help="Would be logs writing to a file. Default yes.",
)
def cli(verbose, no_log_file):
    logging.setLoggerClass(BotLogger)
    logger.setup(verbose, no_log_file=no_log_file)


@cli.command()
def start():
    click.echo("Start: ")
    try:
        asyncio.run(
            dispatcher.start_polling(
                bot, config=config
            )
        )
    finally:
        click.echo("Shutdown...")


@cli.command()
def migrate():
    start_migrate()
    click.echo("Done!")


@cli.command()
def create_tables():
    _create_tables()


if __name__ == "__main__":
    cli()
