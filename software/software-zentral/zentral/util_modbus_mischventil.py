import enum
from typing import List

from zentral.util_modbus import MODBUS_BELIMO_MAX_REGISTER_COUNT, MODBUS_BELIMO_MAX_REGISTER_START_ADDRESS
from zentral.util_modbus_wrapper import ModbusWrapper


class EnumRegisters(enum.IntEnum):
    """
    See: https://www.belimo.com/mam/general-documents/system_integration/Modbus/belimo_Modbus-Register_Energy-Valve_v4_01_en-gb.pdf
    """

    SETPOINT = 0
    "Setpoint [%] [0.0 .. 1.0]"
    RELATIVE_POSITION = 4
    "Relative Position [%] [0.0 .. 1.0]"
    ZENTRAL_FLUSS_M3_S = 7
    "Absolute volumetric flow [l/s] 0…45 l/s"
    ZENTRAL_COOLING_ENERGIE_J = 65
    "Cooling Energy [kWh]"
    ZENTRAL_HEATING_ENERGIE_J = 71
    "Heating Energy [kWh]"
    ZENTRAL_VALVE_T1_C = 19
    "Temperature 1 (external) [°C]"
    ZENTRAL_VALVE_T2_C = 21
    "Temperature 2 (integrated) [°C]"
    ZENTRAL_COOLING_POWER_W = 27
    "Absolute cooling power [kW]"
    ZENTRAL_HEATING_POWER_W = 33
    "Absolute heating power [kW]"
    ABSOLUTE_POWER_W = 166
    "Absolute Pmax [kW]"


class MischventilRegisters:
    def __init__(self, registers: List[int]):
        assert len(registers) == MODBUS_BELIMO_MAX_REGISTER_COUNT
        self._registers = registers

    @property
    def setpoint(self) -> float:
        "r/w [0..1]"
        return self._read_16bit(EnumRegisters.SETPOINT, factor=1e-4)

    @property
    def relative_position(self) -> float:
        "r [0..1]"
        return self._read_16bit(EnumRegisters.RELATIVE_POSITION, factor=1e-4)

    @property
    def fluss_m3_s(self) -> float:
        return self._read_16bit(EnumRegisters.ZENTRAL_FLUSS_M3_S, factor=1e-5)

    @property
    def valve_T1_C(self) -> float:
        return self._read_16bit(EnumRegisters.ZENTRAL_VALVE_T1_C, factor=0.01)

    @property
    def valve_T2_C(self) -> float:
        return self._read_16bit(EnumRegisters.ZENTRAL_VALVE_T2_C, factor=0.01)

    @property
    def cooling_energie_J(self) -> float:
        return self._read_32bit(EnumRegisters.ZENTRAL_COOLING_ENERGIE_J, factor=3.6e6)

    @property
    def heating_energie_J(self) -> float:
        return self._read_32bit(EnumRegisters.ZENTRAL_HEATING_ENERGIE_J, factor=3.6e6)

    @property
    def cooling_power_W(self) -> float:
        return self._read_32bit(EnumRegisters.ZENTRAL_COOLING_POWER_W, factor=1.0)

    @property
    def heating_power_W(self) -> float:
        return self._read_32bit(EnumRegisters.ZENTRAL_HEATING_POWER_W, factor=1.0)

    @property
    def absolute_power_W(self) -> float:
        return self._read_32bit(EnumRegisters.ABSOLUTE_POWER_W, factor=1.0)

    def _read_16bit(self, address: int, factor: float) -> float:
        return self._registers[address] * factor

    def _read_32bit(self, address: int, factor: float) -> float:
        assert len(self._registers) > address + 2
        # See page 2 of https://www.belimo.com/mam/general-documents/system_integration/Modbus/belimo_Modbus-Register_Energy-Valve_v4_01_en-gb.pdf
        value = (self._registers[address + 1] << 16) + self._registers[address]

        return value * factor


class Mischventil:
    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Mischventil(modbus={self._modbus_address})"

    @property
    async def all_registers(self) -> List[int]:
        """
        Try to read as many bytes as possible.
        """
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=MODBUS_BELIMO_MAX_REGISTER_START_ADDRESS,
            count=MODBUS_BELIMO_MAX_REGISTER_COUNT,
        )
        assert not response.isError()
        return response.registers

    @property
    async def setpoint(self) -> float:
        "r/w [0..1]"
        return await self._read_16bit(EnumRegisters.SETPOINT, factor=1e-4)

    async def setpoint_set(self, value: float) -> None:
        "r/w [0..1]"
        assert 0.0 <= value <= 1.0
        await self._write_16bit(EnumRegisters.SETPOINT, value, factor=1e-4)

    async def _read_16bit(self, address: int, factor: float) -> float:
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=address,
            count=1,
        )
        return response.registers[0] * factor

    async def _write_16bit(self, address: int, value: float, factor: float) -> None:
        value_raw = round(value / factor)
        assert 0 <= value_raw < 2**16
        await self._modbus.write_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=address,
            values=[value_raw],
        )

    async def _read_32bit(self, address: int, factor: float) -> float:
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=address,
            count=2,
        )
        assert not response.isError()

        # See page 2 of https://www.belimo.com/mam/general-documents/system_integration/Modbus/belimo_Modbus-Register_Energy-Valve_v4_01_en-gb.pdf
        value = (response.registers[1] << 16) + response.registers[address]
        return value * factor
