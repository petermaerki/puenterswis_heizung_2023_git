# scripts/example/simple_rtu_client.py
import asyncio
import fcntl
import logging
import os
import pathlib
import struct
import sys
import time

import asyncssh
from ptpython.contrib.asyncssh_repl import ReplSSHServerSession
from ptpython.repl import embed
from pymodbus import Framer, ModbusException
from pymodbus.client import AsyncModbusSerialClient
from serial.tools import list_ports

import config_base
import config_bochs

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()
DIRECTORY_MICROPYTHON = (
    DIRECTORY_OF_THIS_FILE.parent.parent / "software-dezentral" / "micropython"
)
assert DIRECTORY_MICROPYTHON.is_dir()
sys.path.append(str(DIRECTORY_MICROPYTHON))

import portable_modbus_registers

modbus_time_1char_ms = 11 / 9600


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def find_serial_port() -> str:
    ports = list(list_ports.comports())
    ports.sort(key=lambda p: p.device)
    if True:
        # Waveshare USB to RS485
        vid = 0x0403  # Vendor Id
        pid = 0x6001  # Product Id
        product = "FT232R USB UART"
    if False:
        # Waveshare USB to RS485 (B)
        vid = 0x1A86  # Vendor Id
        pid = 0x55D3  # Product Id
        product = "USB Single Serial"
    if False:
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

    if False:
        fh = port.fileno()

        # A struct with configuration for serial port.
        serial_rs485 = struct.pack("hhhhhhhh", 1, 0, 0, 0, 0, 0, 0, 0)
        fcntl.ioctl(fh, 0x542F, serial_rs485)

    return client


async def interactive_shell() -> None:
    """
    Coroutine that starts a Python REPL from which we can access the global
    counter variable.
    """
    print(
        'You should be able to read and update the "counter[0]" variable from this shell.'
    )
    try:
        await embed(globals=globals(), return_asyncio_coroutine=True, patch_stdout=True)
    except EOFError:
        # Stop the loop when quitting the repl. (Ctrl-D press.)
        loop.stop()


class MySSHServer(asyncssh.SSHServer):
    """
    Server without authentication, running `ReplSSHServerSession`.
    """

    def __init__(self, get_namespace):
        print(f"Connected {get_namespace()}")
        self.get_namespace = get_namespace
        os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"

    def begin_auth(self, username):
        # No authentication.
        print("No authentication")
        return False

    def session_requested(self):
        print("session_requested")
        print(f"{ReplSSHServerSession=}")
        session = ReplSSHServerSession(self.get_namespace)
        print(f"{session=}")
        return session


async def main(port: int = 8222):
    # Namespace exposed in the REPL.
    environ = {"hello": "world"}

    # Start SSH server.
    def create_server() -> MySSHServer:
        return MySSHServer(lambda: environ)

    print("Listening on :%i" % port)
    print('To connect, do "ssh localhost -p %i"' % port)

    await asyncssh.create_server(
        create_server,
        "",
        port,
        server_host_keys=["/home/maerki/.ssh/id_rsa"]
        # server_host_keys=["/etc/ssh/ssh_host_dsa_key"]
    )

    # await interactive_shell()
    await asyncio.Future()  # Wait forever.
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
