
from mp.util_serial import find_serial_port, FindArguments, SerialPortNotFoundException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus import Framer


modbus_time_1char_ms = 11 / 9600


def get_serial_port2():
    for args in (
        # Waveshare "USB TO 4CH RS485"
        FindArguments(vid=0x1A86, pid=0x55D5, n=0),
        # Waveshare "USB TO RS485"
        FindArguments(vid=0x0403, pid=0x6001, n=0),
    ):
        try:
            return find_serial_port(args)
        except SerialPortNotFoundException:
            continue
    raise AttributeError("No Modbus USB found!")


def get_modbus_client() -> AsyncModbusSerialClient:
    """
    Return serial.Serial instance, ready to use for RS485.
    """
    port = get_serial_port2()
    client = AsyncModbusSerialClient(
        port=port,
        framer=Framer.RTU,
        baudrate=9600,
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
