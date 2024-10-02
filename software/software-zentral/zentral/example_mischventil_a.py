# scripts/example/simple_rtu_client.py
# pylint: disable=all
import asyncio
import enum
import logging

from pymodbus import Framer
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.payload import BinaryPayloadDecoder
from serial.tools import list_ports

modbus_time_1char_ms = 11 / 9600


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

MODBUS_ADDRESS_RELAIS = 1
MODBUS_ADDRESS_BELIMO = 3


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
    def __init__(self, modbus):
        self._modbus = modbus

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
            slave=MODBUS_ADDRESS_BELIMO, address=address, count=1
        )
        return response.registers[0] * factor

    async def _write_16bit(self, address: int, value: float, factor: float) -> float:
        value_raw = round(value / factor)
        assert 0 <= value_raw < 2**16
        response = await self._modbus.write_registers(
            slave=MODBUS_ADDRESS_BELIMO, address=address, values=[value_raw]
        )

    async def _read_32bit(self, address: int, factor: float) -> float:
        response = await self._modbus.read_holding_registers(
            slave=MODBUS_ADDRESS_BELIMO, address=address, count=2
        )
        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers,
            byteorder=Endian.LITTLE,
            wordorder=Endian.LITTLE,
        )

        value = decoder.decode_32bit_uint()

        return value * factor


class Relais:
    def __init__(self, modbus):
        self._modbus = modbus

    async def relais_set_obsolete(self):
        for coils in ([1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 1]):
            response = await self._modbus.write_coils(
                slave=MODBUS_ADDRESS_RELAIS,
                address=0,
                values=coils,
            )
            print(response)

            response = await self._modbus.read_coils(
                slave=MODBUS_ADDRESS_RELAIS,
                address=0,
                count=8,
            )
            print(response)
            await asyncio.sleep(0.5)

    async def set(self, list_relays: tuple[bool]) -> None:
        assert isinstance(list_relays, (list, tuple))
        assert len(list_relays) == 8
        response = await self._modbus.write_coils(
            slave=MODBUS_ADDRESS_RELAIS,
            address=0,
            values=list_relays,
        )


def find_serial_port() -> str:
    ports = list(list_ports.comports())
    ports.sort(key=lambda p: p.device)
    if False:
        # Waveshare USB to RS485
        vid = 0x0403  # Vendor Id
        pid = 0x6001  # Product Id
        product = "FT232R USB UART"
    if False:
        # Waveshare USB to RS485 (B)
        vid = 0x1A86  # Vendor Id
        pid = 0x55D3  # Product Id
        product = "USB Single Serial"
    if True:
        # Waveshare USB to 4Ch RS485
        vid = 0x1A86  # Vendor Id
        pid = 21973  # Product Id
        product = "USB Quad_Serial"
    if False:
        vid = 1027  # Vendor Id
        pid = 0x55D3  # Product Id
        # product = "USB-RS485 Cable"

    for port in ports:
        # if port.product != product:
        #     continue
        if port.pid != pid:
            continue
        if port.vid != vid:
            continue
        return port.device

    raise Exception(f"No serial interface found for {vid=} {product=}")


def get_modbus_client():
    if True:
        port = find_serial_port()
        # Return serial.Serial instance, ready to use for RS485.
        client = AsyncModbusSerialClient(
            port=port,
            framer=Framer.RTU,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1.0,  # :param timeout: Timeout for a request, in seconds.
            retries=1,  # TODO: 1 or 0? # :param retries: Max number of retries per request.
            retry_on_empty=0,  # :param retry_on_empty: Retry on empty response.
            broadcast_enable=False,  # :param broadcast_enable: True to treat id 0 as broadcast address.
            reconnect_delay=0.3,  # :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
            reconnect_delay_max=1.0,  # :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
        )
    if False:
        port = find_serial_port()
        # Return serial.Serial instance, ready to use for RS485.
        client = AsyncModbusSerialClient(
            port=port,
            framer=Framer.RTU,
            baudrate=38400,
            bytesize=8,
            parity="N",
            stopbits=2,
            timeout=1.0,  # :param timeout: Timeout for a request, in seconds.
            retries=1,  # TODO: 1 or 0? # :param retries: Max number of retries per request.
            retry_on_empty=0,  # :param retry_on_empty: Retry on empty response.
            broadcast_enable=True,  # :param broadcast_enable: True to treat id 0 as broadcast address.
            reconnect_delay=0.3,  # :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
            reconnect_delay_max=1.0,  # :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
        )
    if False:
        client = AsyncModbusTcpClient(host="10.0.1.145", port=502, framer=Framer.SOCKET)

    return client


async def scan_modbus_slaves(modbus):
    # for i in range(1, 247):
    for i in range(1, 4):
        try:
            response = await modbus.read_coils(
                slave=i,
                address=0,
                count=8,
            )

            # response = await modbus.read_device_information(
            #     slave=i,  # MODBUS_ADDRESS_BELIMO,
            #     address=2,  # EnumRegisters.SETPOINT.value,
            #     count=1,
            # )
            print(f"{i}: found: {response}")
        except ConnectionException as exc:
            print(f"{i}: {exc}")
            # await modbus.reconnect()
        except ModbusIOException as exc:
            print(f"{i}: {exc}")
            # await modbus.reconnect()
        await asyncio.sleep(2.0)


async def call_belimo(modbus):
    # response = await modbus.read_input_registers(
    #     slave=MODBUS_ADDRESS_BELIMO,
    #     address=20,  # EnumRegisters.SETPOINT.value,
    #     count=1,
    # )
    # print(response)
    response = await modbus.read_holding_registers(
        slave=MODBUS_ADDRESS_BELIMO,
        address=20,  # EnumRegisters.SETPOINT.value,
        count=1,
    )
    print(response)


async def main():
    modbus = get_modbus_client()
    await modbus.connect()

    r = Relais(modbus)
    await r.set(list_relays=(True, True, False, False, False, False, False, False))
    await r.set(list_relays=(False, True, False, False, False, False, False, False))

    await call_belimo(modbus)
    m = Mischventil(modbus=modbus)
    print(f"{await m.absolute_power_kW=}")
    print(f"{await m.zentral_fluss_m3_S=}")
    print(f"{await m.zentral_valve_T1_C=}")
    print(f"{await m.zentral_valve_T2_C=}")
    print(f"{await m.zentral_cooling_energie_J=}")
    print(f"{await m.zentral_heating_energie_J=}")
    print(f"{await m.zentral_cooling_power_W=}")
    print(f"{await m.zentral_heating_power_W=}")
    print(f"{ await m.relative_position=}")
    if False:
        # await relais(modbus)
        # await scan_modbus_slaves(modbus)
        new_setpoint = 0.6 if await m.setpoint < 0.55 else 0.5
        await m.setpoint_set(new_setpoint)
        print(f"{await m.setpoint=}")
        while True:
            relative_position = await m.relative_position
            diff = relative_position - new_setpoint
            print(f"{new_setpoint=:0.2f} {relative_position=:0.2f} {diff=:0.2f}")
            if abs(relative_position - new_setpoint) < 0.01:
                break
            await asyncio.sleep(1.0)

    modbus.close()
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
