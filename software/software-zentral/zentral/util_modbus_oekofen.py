import enum
import logging
import time
from typing import List

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from zentral.constants import DIRECTORY_LOG
from zentral.util_modbus import MODBUS_OEKOFEN_MAX_REGISTER_COUNT, MODBUS_OEKOFEN_MAX_REGISTER_START_ADDRESS
from zentral.util_modbus_oekofen_regs import DICT_REG_DEFS, REG_DEFS, RegDefC, RegDefI
from zentral.util_modbus_wrapper import ModbusWrapper

logger = logging.getLogger(__name__)


class FA_Mode(enum.IntEnum):
    OFF = 0
    AUTO = 1
    ON = 2
    UNKNOWN = 1000

    @classmethod
    def _missing_(cls, value):
        logger.warning(f"Unknown value={value}")
        return cls.UNKNOWN


class FA_State(enum.IntEnum):
    PERMANENT = 0
    START = 1
    IGNITION = 2
    SOFTSTART = 3
    HEATING_FULL_POWER = 4
    RUN_ON_TIME = 5
    OFF = 6
    SUCTION = 7
    ASH = 8
    PELLET = 9
    PELLET_SWITCH = 10
    STOERUNG = 11
    EINMESSEN = 12
    OFF99 = 99
    UNKNOWN = 1000

    @classmethod
    def _missing_(cls, value):
        logger.warning(f"Unknown value={value}")
        if cls.EINMESSEN < value < cls.OFF99:
            return cls.OFF99
        return cls.UNKNOWN


class OekofenRegisters:
    def __init__(self, registers: List[int]):
        assert len(registers) == MODBUS_OEKOFEN_MAX_REGISTER_COUNT
        self._registers = registers

    def append_to_file(self) -> None:
        filename = DIRECTORY_LOG / "oekofen_registers.data"
        _TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

        file_exists = filename.exists()
        with filename.open("a") as f:
            if not file_exists:
                values = "now", "time", *[reg.name for reg in REG_DEFS]
                f.write(" ".join(values))
                f.write("\n")

            now = time.time()
            time_ = time.strftime(_TIMESTAMP_FORMAT, time.localtime(now))
            values = format(now, "0.0f"), time_, *[self.attr_str(reg.name) for reg in REG_DEFS]

            f.write(" ".join(values))
            f.write("\n")

    def get_influx_fields(self, prefix: str) -> dict[str, float | int]:
        return {prefix + reg.name: self.attr_value(reg.name) for reg in REG_DEFS}

    def attr_value(self, attribute_name: str) -> int | float:
        reg_def = DICT_REG_DEFS[attribute_name]
        if isinstance(reg_def, RegDefC):
            return self._read_16bit_float(reg_def.address, factor=0.1)
        return self._read_16bit_int(reg_def.address)

    def attr_str(self, attribute_name: str) -> int | float:
        v = self.attr_value(attribute_name=attribute_name)
        if isinstance(v, float):
            return format(v, "2.1f")
        return format(v, "d")

    def _read_16bit_int(self, address: int) -> int:
        return self._registers[address]

    def _read_16bit_float(self, address: int, factor: float) -> float:
        return self._registers[address] * factor

    def _read_32bit(self, address: int, factor: float) -> float:
        assert len(self._registers) > address + 2
        decoder = BinaryPayloadDecoder.fromRegisters(
            self._registers[address : address + 2],
            byteorder=Endian.LITTLE,
            wordorder=Endian.LITTLE,
        )

        value = decoder.decode_32bit_uint()

        return value * factor

    def attr_value2(self, brenner: int, attribute_template: str) -> int | float:
        """
        Example:
          brenner = 1
          attribute_template = "FAx_STATE
        ->
          attribute_name = "FA1_STATE
        """
        assert 1 <= brenner <= 2
        attribute_name = attribute_template.replace("x", str(brenner))
        return self.attr_value(attribute_name=attribute_name)

    def modulation_percent(self, brenner: int) -> int:
        return self.attr_value2(brenner=brenner, attribute_template="FAx_MODULATION_PERCENT")

    def fa_state(self, brenner: int) -> FA_State:
        v = self.attr_value2(brenner=brenner, attribute_template="FAx_STATE")
        return FA_State(v)

    def fa_mode(self, brenner: int) -> FA_Mode:
        v = self.attr_value2(brenner=brenner, attribute_template="FAx_MODE")
        return FA_Mode(v)


class Oekofen:
    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Oekofen(modbus={self._modbus_address})"

    @property
    async def all_registers(self) -> List[int]:
        """
        Try to read as many bytes as possible.
        """
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=MODBUS_OEKOFEN_MAX_REGISTER_START_ADDRESS,
            count=MODBUS_OEKOFEN_MAX_REGISTER_COUNT,
        )
        assert not response.isError()
        return response.registers

    async def set_register(self, name: str, value: float) -> None:
        assert isinstance(name, str)
        assert isinstance(value, float)
        reg_def = DICT_REG_DEFS[name]
        assert isinstance(reg_def, RegDefI | RegDefC)
        factor = 0.1 if isinstance(reg_def, RegDefC) else 1.0
        await self._write_16bit(name=name, address=reg_def.address, value=value, factor=factor)

    async def _write_16bit(self, name: str, address: int, value: float, factor: float) -> None:
        value_raw = round(value / factor)
        assert 0 <= value_raw < 2**16

        logger.info(f"Oekofen set register {name}({address}) to {value:0.1f}({value_raw})")

        await self._modbus.write_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=address,
            values=[value_raw],
        )
