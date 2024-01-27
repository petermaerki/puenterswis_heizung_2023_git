import enum

from pymodbus import ModbusException
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client import AsyncModbusSerialClient


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
    ABSOLUTE_POWER_kW = 166
    "Absolute Pmax [kW]"


class Mischventil:
    def __init__(self, modbus: AsyncModbusSerialClient, modbus_address: int):
        self._modbus = modbus
        self._modbus_address = modbus_address

    @property
    async def setpoint(self) -> float:
        "r/w [0..1]"
        return await self._read_16bit(EnumRegisters.SETPOINT, factor=1e-4)

    async def setpoint_set(self, value: float) -> None:
        "r/w [0..1]"
        assert 0.0 <= value <= 1.0
        await self._write_16bit(EnumRegisters.SETPOINT, value, factor=1e-4)

    @property
    async def relative_position(self) -> float:
        "r [0..1]"
        return await self._read_16bit(EnumRegisters.RELATIVE_POSITION, factor=1e-4)

    @property
    async def zentral_fluss_m3_S(self) -> float:
        return await self._read_16bit(EnumRegisters.ZENTRAL_FLUSS_M3_S, factor=1e-5)

    @property
    async def zentral_valve_T1_C(self) -> float:
        return await self._read_16bit(EnumRegisters.ZENTRAL_VALVE_T1_C, factor=0.01)

    @property
    async def zentral_valve_T2_C(self) -> float:
        return await self._read_16bit(EnumRegisters.ZENTRAL_VALVE_T2_C, factor=0.01)

    @property
    async def zentral_cooling_energie_J(self) -> float:
        return await self._read_32bit(
            EnumRegisters.ZENTRAL_COOLING_ENERGIE_J, factor=3.6e6
        )

    @property
    async def zentral_heating_energie_J(self) -> float:
        return await self._read_32bit(
            EnumRegisters.ZENTRAL_HEATING_ENERGIE_J, factor=3.6e6
        )

    @property
    async def zentral_cooling_power_W(self) -> float:
        return await self._read_32bit(EnumRegisters.ZENTRAL_COOLING_POWER_W, factor=1.0)

    @property
    async def zentral_heating_power_W(self) -> float:
        return await self._read_32bit(EnumRegisters.ZENTRAL_HEATING_POWER_W, factor=1.0)

    @property
    async def absolute_power_kW(self) -> float:
        return await self._read_32bit(EnumRegisters.ABSOLUTE_POWER_kW, factor=0.001)

    async def _read_16bit(self, address: int, factor: float) -> float:
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address, address=address, count=1
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        return response.registers[0] * factor

    async def _write_16bit(self, address: int, value: float, factor: float) -> float:
        value_raw = round(value / factor)
        assert 0 <= value_raw < 2**16
        response = await self._modbus.write_registers(
            slave=MODBUS_ADDRESS_BELIMO, address=address, values=[value_raw]
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

    async def _read_32bit(self, address: int, factor: float) -> float:
        response = await self._modbus.read_holding_registers(
            slave=self._modbus_address, address=address, count=2
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers,
            byteorder=Endian.LITTLE,
            wordorder=Endian.LITTLE,
        )

        value = decoder.decode_32bit_uint()

        return value * factor
