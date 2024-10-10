from __future__ import annotations

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
from zentral.util_modulation_soll import BrennerZustaende, BrennerZustand

logger = logging.getLogger(__name__)


class FlashWriteLimiter:
    """
    We allow 20 flash writes in a 12h window.
    A 12h window starts at a arbitary time.
    If the window ends, automatically a new windows is started.
    """

    WINDOW_DURATION_H = 12.0
    ALLOWED_FLASH_WRITES = 20

    def __init__(self) -> None:
        self.window_end_s = 0.0
        self.flash_write_counter = 0

    def allowed_to_write_flash(self, now_s: float) -> bool:
        """
        Returns True if we are allowed to write.

        Every WINDOW_DURATION_H: A logger info with the flash write count.
        If to many flashes: A logger warning will be printed.
        """
        if now_s > self.window_end_s:
            # A new window starts
            if self.window_end_s > 0.0:
                logger.warning(f"FlashWriteLimiter: start a new window of {self.WINDOW_DURATION_H}h. {self.flash_write_counter} writes, limit {self.ALLOWED_FLASH_WRITES} writes.")

            self.flash_write_counter = 0
            self.window_end_s = now_s + self.WINDOW_DURATION_H * 60.0 * 60.0

        self.flash_write_counter += 1

        if self.flash_write_counter > self.ALLOWED_FLASH_WRITES:
            logger.warning(f"FlashWriteLimiter: disallow write after {self.flash_write_counter} of {self.ALLOWED_FLASH_WRITES} writes.")
            return False

        return True


class PlantMode(enum.IntEnum):
    """
    TouchScreen Menu: Betriebsart
    """

    OFF = 0
    """
    TouchScreen Menu: Betriebsart Anlage aus
    """
    AUTO = 1
    DEMESTIC_HOTWATER = 2
    UNKNOWN = 1000

    @classmethod
    def _missing_(cls, value):
        logger.warning(f"Unknown value={value}")
        return cls.UNKNOWN


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
    """
    Im Touch Screen: Leistungsbrand
    """
    RUN_ON_TIME = 5
    """
    Im Touch Screen: "Nachlauf"
    """
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
        return {prefix + reg.name: self._attr_value(reg.name) for reg in REG_DEFS}

    def _attr_value(self, attribute_name: str) -> int | float:
        reg_def = DICT_REG_DEFS[attribute_name]
        if isinstance(reg_def, RegDefC):
            return self._read_16bit_float(reg_def.address, factor=0.1)
        return self._read_16bit_int(reg_def.address)

    def attr_str(self, attribute_name: str) -> int | float:
        v = self._attr_value(attribute_name=attribute_name)
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

    def _get_register_name(self, brenner_idx1: int, attribute_template: str) -> str:
        """
        Example:
          brenner = 1
          attribute_template = "FAx_STATE
        ->
          attribute_name = "FA1_STATE
        """
        assert 1 <= brenner_idx1 <= 2
        return attribute_template.replace("x", str(brenner_idx1))

    def _attr_value2(self, brenner_idx1: int, attribute_template: str) -> int | float:
        attribute_name = self._get_register_name(brenner_idx1=brenner_idx1, attribute_template=attribute_template)
        return self._attr_value(attribute_name=attribute_name)

    def modulation_percent(self, brenner_idx1: int) -> int:
        return self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_MODULATION_PERCENT")

    def fa_state(self, brenner_idx1: int) -> FA_State:
        v = self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_STATE")
        return FA_State(v)

    def fa_mode(self, brenner_idx1: int) -> FA_Mode:
        v = self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_MODE")
        return FA_Mode(v)

    def fa_temp_C(self, brenner_idx1: int) -> float:
        return self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_TEMP_C")

    def fa_runtime_h(self, brenner_idx1: int) -> int:
        return self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_RUNTIME_H")

    def verfuegbar(self, brenner_idx1: int) -> bool:
        return (self.plant_mode() is PlantMode.AUTO) and (self.fa_mode(brenner_idx1=brenner_idx1) is FA_Mode.AUTO)

    def zuendet_oder_brennt(self, brenner_idx1: int) -> bool:
        return FA_State.IGNITION <= self.fa_state(brenner_idx1=brenner_idx1) <= FA_State.RUN_ON_TIME

    def brennt(self, brenner_idx1: int) -> bool:
        return self.fa_state(brenner_idx1=brenner_idx1) == FA_State.HEATING_FULL_POWER

    def plant_mode(self) -> PlantMode:
        v = self._attr_value(attribute_name="PLANT_MODE")
        return PlantMode(v)

    def uw_temp_on_C(self, brenner_idx1: int) -> float:
        return self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_UW_TEMP_ON_C")

    def regel_temp_C(self, brenner_idx1: int) -> float:
        return self._attr_value2(brenner_idx1=brenner_idx1, attribute_template="FAx_REGEL_TEMP_C")

    async def set_regel_temp_C(self, oekofen: Oekofen, brenner_idx1: int, temp_C: float) -> None:
        attribute_name = self._get_register_name(brenner_idx1=brenner_idx1, attribute_template="FAx_REGEL_TEMP_C")
        await oekofen.set_register(name=attribute_name, value=temp_C)

    @property
    def brenner_zustaende(self) -> BrennerZustaende:
        def f(brenner_idx1):
            return BrennerZustand(
                fa_temp_C=self.fa_temp_C(brenner_idx1),
                fa_runtime_h=self.fa_runtime_h(brenner_idx1),
                verfuegbar=self.verfuegbar(brenner_idx1),
                zuendet_oder_brennt=self.zuendet_oder_brennt(brenner_idx1),
                brennt=self.brennt(brenner_idx1),
            )

        return BrennerZustaende([f(brenner_idx1) for brenner_idx1 in (1, 2)])


class Oekofen:
    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Oekofen(modbus={self._modbus_address})"
        self._flash_write_limiter = FlashWriteLimiter()

    def allowed_to_write_flash(self) -> bool:
        return self._flash_write_limiter.allowed_to_write_flash(now_s=time.monotonic())

    @property
    async def all_registers(self) -> list[int]:
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
