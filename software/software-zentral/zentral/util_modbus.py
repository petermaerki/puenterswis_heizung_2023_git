import logging

from mp.util_serial import FindArguments, SerialPortNotFoundException, find_serial_port
from pymodbus import Framer
from pymodbus.client import AsyncModbusSerialClient

logger = logging.getLogger(__name__)

modbus_time_1char_ms = 11 / 9600

MODBUS_BELIMO_MAX_REGISTER_START_ADDRESS = 0
MODBUS_BELIMO_MAX_REGISTER_COUNT = 125
"""
Some sources say that a modbus packet should not exceet 256 bytes => 125 holding registers
"""
MODBUS_OEKOFEN_MAX_REGISTER_START_ADDRESS = 0
MODBUS_OEKOFEN_MAX_REGISTER_COUNT = 95

MODBUS_TIMEOUT_S = 0.4
"""
This timeout was 0.1s, but this limited the read of the maximum register count to
~50 registers.
Maximum of 125 registers:
 0.28s fails
 0.29s ok
=> We choose 0.4s
"""


def get_serial_port2(n: int):
    """
    n=0: first port
    n=1: second port
    """
    for args in (
        # Waveshare "USB TO 4CH RS485"
        FindArguments(vid=0x1A86, pid=0x55D5, n=n),
        # Waveshare "USB TO RS485"
        FindArguments(vid=0x0403, pid=0x6001, n=0),
    ):
        try:
            return find_serial_port(args)
        except SerialPortNotFoundException:
            continue
    raise AttributeError("No Modbus USB found!")


def get_modbus_client(n: int, baudrate: int) -> AsyncModbusSerialClient:
    """
    Return serial.Serial instance, ready to use for RS485.

    n=0: first port
    n=1: second port

    baudrate=9600
    baudrate=19200
    """
    assert isinstance(n, int)
    assert n in (0, 1)
    assert isinstance(baudrate, int)
    assert baudrate in (9600, 19200)
    port = get_serial_port2(n=n)

    class MyAsyncModbusSerialClient(AsyncModbusSerialClient):
        def close(self, reconnect: bool = False) -> None:
            logger.debug(f"MyAsyncModbusSerialClient: close({reconnect=})")
            if reconnect is True:
                self.framer.resetFrame()
                self.recv_buffer = b""
                self.sent_buffer = b""
                return
            super().close(reconnect=False)

    client = MyAsyncModbusSerialClient(
        port=port,
        framer=Framer.RTU,
        baudrate=baudrate,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=MODBUS_TIMEOUT_S,  # :param timeout: Timeout for a request, in seconds.
        retries=0,  # :param retries: Max number of retries per request.
        retry_on_empty=0,  # :param retry_on_empty: Retry on empty response.
        broadcast_enable=False,  # :param broadcast_enable: True to treat id 0 as broadcast address.
        reconnect_delay=0.3,  # :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
        reconnect_delay_max=1.0,  # :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    )

    return client
