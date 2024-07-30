import logging

from mp.util_serial import find_serial_port, FindArguments, SerialPortNotFoundException
from pymodbus.client import AsyncModbusSerialClient
from pymodbus import Framer

logger = logging.getLogger(__name__)

modbus_time_1char_ms = 11 / 9600

MODBUS_MAX_REGISTER_START_ADDRESS = 1
MODBUS_MAX_REGISTER_COUNT = 125
"""
Some sources say that a modbus packet should not exceet 256 bytes => 125 holding registers
"""

MODBUS_TIMEOUT_S = 0.4
"""
This timeout was 0.1s, but this limited the read of the maximum register count to
~50 registers.
Maximum of 125 registers:
 0.28s fails
 0.29s ok
=> We choose 0.4s
"""


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

    # class MyClient(AsyncModbusSerialClient):
    #     def close(self, reconnect: bool = False) -> None:
    #         super().close(reconnect=False)

    class MyAsyncModbusSerialClient(AsyncModbusSerialClient):
        def close(self, reconnect: bool = False) -> None:
            logger.debug(f"MyAsyncModbusSerialClient: close({reconnect=})")
            if reconnect is True:
                self.framer.resetFrame()
                self.recv_buffer = b""
                self.sent_buffer = b""
                return
            super().close(reconnect=False)

        # async def async_execute(self, request=None):
        #     # await super().async_execute(request)
        #     request.transaction_id = self.transaction.getNextTID()
        #     packet = self.framer.buildPacket(request)

        #     count = 0
        #     while count <= self.retries:
        #         req = self.build_response(request.transaction_id)
        #         if not count or not self.no_resend_on_retry:
        #             self.transport_send(packet)
        #         if self.broadcast_enable and not request.slave_id:
        #             resp = b"Broadcast write sent - no response expected"
        #             break
        #         try:
        #             resp = await asyncio.wait_for(
        #                 req, timeout=self.comm_params.timeout_connect
        #             )
        #             break
        #         except asyncio.exceptions.TimeoutError:
        #             count += 1
        #     if count > self.retries:
        #         self.close(reconnect=True)
        #         raise ModbusIOException(
        #             f"ERROR: No response received after {self.retries} retries"
        #         )

        #     return resp

    client = MyAsyncModbusSerialClient(
        port=port,
        framer=Framer.RTU,
        baudrate=9600,
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
