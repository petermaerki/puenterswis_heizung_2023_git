# scripts/example/simple_rtu_client.py
import asyncio
import logging

from pymodbus import Framer
from pymodbus.client import AsyncModbusSerialClient
from serial.tools import list_ports

modbus_time_1char_ms = 11 / 9600


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


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
    port = find_serial_port()
    """Return serial.Serial instance, ready to use for RS485."""
    client = AsyncModbusSerialClient(
        port=port,
        framer=Framer.RTU,
        baudrate=9200,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=0.1,  # :param timeout: Timeout for a request, in seconds.
        retries=0,  # TODO: 1 or 0? # :param retries: Max number of retries per request.
        retry_on_empty=0,  # :param retry_on_empty: Retry on empty response.
        broadcast_enable=False,  # :param broadcast_enable: True to treat id 0 as broadcast address.
        reconnect_delay=0.3,  # :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
        reconnect_delay_max=1.0,  # :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    )

    return client


async def call_belimo():
    modbus = get_modbus_client()
    await modbus.connect()

    response = await modbus.read_input_registers(
        slave=42,
        address=123,
        count=3,
    )
    print(response)
    modbus.close()


async def main():
    await call_belimo()

    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
