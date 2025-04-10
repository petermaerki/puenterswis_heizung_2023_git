# https://realpython.com/python-logging/

import logging
from logging.handlers import RotatingFileHandler
from typing import List

from hsm.hsm import HsmLoggerProtocol, HsmState  # type: ignore[import]

from zentral.constants import DIRECTORY_LOG

logger = logging.getLogger(__name__)


class HsmLoggingLogger(HsmLoggerProtocol):
    def __init__(self, label: str):
        self._label = label

    def fn_log_debug(self, msg: str) -> None:
        logger.debug(f"{self._label}: {msg}")

    def fn_log_info(self, msg: str) -> None:
        logger.debug(f"{self._label}: {msg}")

    # def fn_state_change(self, _before: HsmState, _after: HsmState) -> None:
    #     logger.warning(
    #         f"{self._prefix}: fn_state_change -> {_before.full_name} --> {_after.full_name}"
    #     )
    def fn_state_change(
        self,
        before: HsmState,
        after: HsmState,
        why: str,
        list_entry_exit: List[str],
    ) -> None:
        if before == after:
            return
        why_text = ""
        if why is not None:
            why_text = f" ({why})"
        text_entry_exit = "==>"
        if len(list_entry_exit) > 0:
            text_entry_exit = f"==>{'==>'.join(list_entry_exit)}==>"
        logger.info(f"{self._label}: {before.full_name} {text_entry_exit} {after.full_name}{why_text}")


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
    # create formatter
    fmt = "%(levelname)s %(filename)s:%(lineno)s %(message)s"
    formatter_stdout = ColorFormatter(fmt=fmt)
    formatter_file = logging.Formatter(fmt="%(asctime)s " + fmt)

    handler_stream = logging.StreamHandler()
    # handler_stream.setLevel(level=logging.INFO)
    handler_stream.setFormatter(formatter_stdout)

    handler_file = RotatingFileHandler(
        DIRECTORY_LOG / "logger.txt",
        mode="a",
        maxBytes=100_000_000,
        backupCount=5,
    )
    # handler_file.setLevel(logging.INFO)
    handler_file.setFormatter(formatter_file)

    logging.basicConfig(handlers=[handler_stream, handler_file], force=True)

    # logging.getLogger("zentral.util_logger").setLevel(logging.DEBUG)
    logging.getLogger("pymodbus.logging").setLevel(logging.INFO)
    logging.getLogger("asyncssh").setLevel(logging.WARNING)
