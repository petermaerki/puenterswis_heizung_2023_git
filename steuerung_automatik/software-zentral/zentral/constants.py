import logging
from pymodbus import ModbusException
import pathlib

logger = logging.getLogger(__name__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_ZENTRAL = DIRECTORY_OF_THIS_FILE.parent
assert (DIRECTORY_ZENTRAL / "zentral").is_dir()

DIRECTORY_REPO = DIRECTORY_ZENTRAL.parent.parent
assert (DIRECTORY_REPO / ".git").is_dir()

DIRECTORY_LOG = DIRECTORY_ZENTRAL / "log"
DIRECTORY_LOG.mkdir(exist_ok=True)

DIRECTORY_DOC = DIRECTORY_ZENTRAL / "doc"
DIRECTORY_DOC.mkdir(exist_ok=True)

MODBUS_ADDRESS_RELAIS = 1
MODBUS_ADDRESS_ADC = 2
MODBUS_ADDRESS_BELIMO = 3

TIMEOUT_AFTER_MODBUS_TRANSFER_S = 0.1

ETAPPE_TAG_VIRGIN = "virgin"
ETAPPE_TAG_BOCHS = "bochs"
ETAPPE_TAG_PUENT = "puent"
ETAPPE_TAGS = (ETAPPE_TAG_VIRGIN, ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT)


class ModbusExceptionIsError(ModbusException):
    pass


class ModbusExceptionRegisterCount(ModbusException):
    pass
