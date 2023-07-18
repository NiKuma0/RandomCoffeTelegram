import logging
import click


class ClickHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            click.echo(msg)
        except Exception:  # pylint: disable=W0718
            self.handleError(record)


class BotLogger(logging.Logger):
    def __init__(
        self, level: int | str = 0,
        file_level: int | str = logging.DEBUG,
        no_log_file: bool = False
    ) -> None:
        super().__init__('randomcoffee', level)
        self.setup(level, file_level, no_log_file)

    def setup(
        self, level: int | str = 0,
        file_level: int | str = logging.DEBUG,
        no_log_file: bool = False
    ) -> None:
        click_handler = ClickHandler(level)
        click_handler.setFormatter(
            logging.Formatter(
                "[%(levelname)s %(asctime)s]\n%(message)s",
                datefmt='"%d/%m %H.%M"',
            )
        )
        file_handler = logging.FileHandler("bot.log")
        file_handler.setLevel(file_level)
        file_handler.setFormatter(logging.Formatter(
            "%(levelname)s:%(name)s:%(asctime)s:%(message)s",
            datefmt='"%d/%m %H.%M"',
        ))
        self.handlers.append(click_handler)
        if not no_log_file:
            self.handlers.append(file_handler)


logger = BotLogger()
