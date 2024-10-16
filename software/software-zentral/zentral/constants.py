import enum
import logging
import pathlib
import sys

from pymodbus import ModbusException

logger = logging.getLogger(__name__)


DEVELOPMENT = True

OEKOFEN_RELAIS_CONTROL_ON = True
"""
In der Testphase, relais nicht schalten
"""

OEKOFEN_MODBUS_CONTROL_ON = True
"""
In der Testphase, modbus nur lesen aber nicht schreiben
"""

ENABLE_OEKOFEN_LOGFILE = True
"""
Write a lot to the sdcard.
"""

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_ZENTRAL = DIRECTORY_OF_THIS_FILE.parent
assert (DIRECTORY_ZENTRAL / "zentral").is_dir()

DIRECTORY_REPO = DIRECTORY_ZENTRAL.parent.parent
assert (DIRECTORY_REPO / ".git").is_dir()

DIRECTORY_LOG = DIRECTORY_ZENTRAL / "log"
DIRECTORY_LOG.mkdir(exist_ok=True)

DIRECTORY_PERSISTENCE = DIRECTORY_ZENTRAL / "persistence"
DIRECTORY_PERSISTENCE.mkdir(exist_ok=True)

DIRECTORY_DOC = DIRECTORY_ZENTRAL / "doc"
DIRECTORY_DOC.mkdir(exist_ok=True)


class Waveshare_4RS232(enum.IntEnum):
    MODBUS_HAEUSER = 0
    MODBUS_OEKOFEN = 1
    MBUS_WAERMEZAEHLER = 2


class ModbusAddressHaeuser(enum.IntEnum):
    RELAIS = 1
    DAC = 2
    BELIMO = 3


class ModbusAddressOeokofen(enum.IntEnum):
    OEKOFEN = 1


ETAPPE_TAG_VIRGIN = "virgin"
ETAPPE_TAG_BOCHS = "bochs"
ETAPPE_TAG_PUENT = "puent"
ETAPPE_TAGS = (ETAPPE_TAG_VIRGIN, ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT)

DEZENTRAL_VERSION_SW_FIXED_RELAIS_VALVE_OPEN = 103


def add_to_path(directory: pathlib.Path) -> None:
    directory_text = str(directory)
    for _dir in sys.path:
        if _dir == directory_text:
            return
    sys.path.append(str(directory))


def add_path_software_zero_dezentral() -> None:
    add_to_path(DIRECTORY_ZENTRAL.parent / "software-zero")
    add_to_path(DIRECTORY_ZENTRAL.parent / "software-dezentral")


class HsmZentralStartupMode(enum.IntEnum):
    Manuell = 0
    AutoSimple = 1
    AutoMischventiltest = 2
    AutoKomplex = 3


class ModbusExceptionIsError(ModbusException):
    """
    Raised on Modbus communication error.
    """


class ModbusExceptionNoResponseReceived(ModbusException):
    """
    "No response received" in e.message
    """


class ModbusExceptionRegisterCount(ModbusException):
    """
    This exception could be raised:
    * If wrong package arrived (unlikly as the checksum will fail too)
    * Due to programming errors (probably).
    """
