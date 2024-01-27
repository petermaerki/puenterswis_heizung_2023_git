import dataclasses
import logging
import pathlib
import warnings
from typing import Callable

logger = logging.getLogger(__name__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_ZERO = DIRECTORY_OF_THIS_FILE.parent
assert (DIRECTORY_ZERO / "rootfs").is_dir()

DIRECTORY_LOG = DIRECTORY_ZERO / "log"
DIRECTORY_LOG.mkdir(exist_ok=True)

DIRECTORY_DOC = DIRECTORY_ZERO / "doc"
DIRECTORY_DOC.mkdir(exist_ok=True)

MODBUS_ADDRESS_RELAIS = 1
MODBUS_ADDRESS_ADC = 2
MODBUS_ADDRESS_BELIMO = 3

TIMEOUT_AFTER_MODBUS_TRANSFER_S = 0.1
