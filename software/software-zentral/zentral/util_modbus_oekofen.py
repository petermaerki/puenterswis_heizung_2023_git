import time
from typing import List

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from zentral.constants import DIRECTORY_LOG
from zentral.util_modbus import MODBUS_OEKOFEN_MAX_REGISTER_COUNT, MODBUS_OEKOFEN_MAX_REGISTER_START_ADDRESS
from zentral.util_modbus_oekofen_regs import DICT_REG_DEFS, REG_DEFS, RegDefC
from zentral.util_modbus_wrapper import ModbusWrapper


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

    def __getattr__(self, attribute_name: str) -> int | float:
        """
        Calling 'x.CASCADE_SET_C' will call this method.
        'attribute_name' is set to 'x.CASCADE_SET_C'.

         throw MissingModbusDataException if no data received yet or communication is broken
        """
        return self.attr_value(attribute_name=attribute_name)

    def attr_value(self, attribute_name: str) -> int | float:
        reg_def = DICT_REG_DEFS[attribute_name]
        if isinstance(reg_def, RegDefC):
            return self._read_16bit_float(reg_def.num, factor=0.1)
        return self._read_16bit_int(reg_def.num)

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
