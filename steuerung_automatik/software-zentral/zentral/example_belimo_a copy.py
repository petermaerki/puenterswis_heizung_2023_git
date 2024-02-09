# scripts/example/simple_rtu_client.py
import asyncio
import enum
import logging

from pymodbus import Framer
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from serial.tools import list_ports

modbus_time_1char_ms = 11 / 9600


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

MODBUS_ADDRESS_BELIMO = 2


class EnumRegisters(enum.IntEnum):
    """
    See: https://www.belimo.com/mam/general-documents/system_integration/Modbus/belimo_Modbus-Register_Energy-Valve_v4_01_en-gb.pdf
    """

    SETPOINT = 0
    "Setpoint [%]	read -> zentral_valve_0_1  0.0. bis 1.0  wert/10000.0"
    ZENTRAL_FLUSS_M3_S = 7
    "Absolute volumetric flow [l/s] 0…45 l/s (0…45‘000) -> zentral_fluss_m3_s   wert/100_000"
    ZENTRAL_COOLING_ENERGIE_J = 65
    "66	65	Cooling Energy [kWh]	-> zentral_cooling_energie_j -> wert*3.6E6"
    ZENTRAL_HEATING_ENERGIE_J = 71
    "72	73	Heating Energy [kWh]	-> zentral_heating_energie_j -> wert*3.6E6"
    ZENTRAL_VALVE_T1_C = 19
    "20	Temperature 1 (external) [°C] ** -> zentral_valve_T1_C wert *100.0"
    ZENTRAL_VALVE_T2_C = 21
    "22	Temperature 2 (integrated) [°C]  -> zentral_valve_T2_C wert *100.0"
    ZENTRAL_COOLING_POWER_W = 27
    "28	Absolute cooling power [kW]  -> zentral_cooling_power_w wert*1.0"
    ZENTRAL_HEATING_POWER_W = 33
    "34	Absolute heating power [kW] -> zentral_heating_power_w	wert*1.0"


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
        pid = 0x55D3  # Product Id
        product = "USB Quad_Serial"

    for port in ports:
        if port.product != product:
            continue
        if port.vid != vid:
            continue
        return port.device

    raise Exception(f"No serial interface found for {vid=} {product=}")


def get_modbus_client():
    if False:
        port = find_serial_port()
        """Return serial.Serial instance, ready to use for RS485."""
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
    if True:
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


async def relais(modbus):
    for coils in ([1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 1]):
        response = await modbus.write_coils(
            slave=1,
            address=0,
            values=coils,
        )
        print(response)

        response = await modbus.read_coils(
            slave=1,
            address=0,
            count=8,
        )
        print(response)
        await asyncio.sleep(0.5)


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

    # await relais(modbus)
    # await scan_modbus_slaves(modbus)
    await call_belimo(modbus)

    modbus.close()
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
