# https://realpython.com/python-logging/

import logging

from hsm.hsm import HsmLogger, HsmMixin, HsmState

from program.constants import DIRECTORY_LOG

logger = logging.getLogger(__name__)


class ZeroLogger(HsmLogger):
    def __init__(
        self,
        hsm: HsmMixin,
    ):
        self._prefix = f"{hsm.__class__.__name__}: "

    def fn_log_debug(self, msg: str) -> None:
        logger.debug(self._prefix + msg)

    def fn_log_info(self, msg: str) -> None:
        logger.info(self._prefix + msg)

    def fn_state_change(self, _before: HsmState, _after: HsmState) -> None:
        logger.warning(
            f"{self._prefix}: fn_state_change -> {_before.full_name} --> {_after.full_name}"
        )


class ColorFormatter(logging.Formatter):
    """
    https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/
    Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629
    """

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def initialize_logger() -> None:
    logging.basicConfig(
        filename=DIRECTORY_LOG / "logger.txt",
        filemode="w",
        format="%(asctime)s %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )

    ch = logging.StreamHandler()
    # ch.setLevel(level=logging.DEBUG)
    ch.setLevel(level=logging.INFO)

    # create formatter
    formatter = ColorFormatter(
        fmt="%(filename)s:%(lineno)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logging.getLogger().addHandler(ch)
