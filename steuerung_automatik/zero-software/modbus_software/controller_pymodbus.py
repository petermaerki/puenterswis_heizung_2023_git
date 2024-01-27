# scripts/example/simple_rtu_client.py
import asyncio

# import fcntl
import logging
import os
import pathlib
import struct
import sys

import asyncssh
import config_base
import config_bochs

# from ptpython.contrib.asyncssh_repl import ReplSSHServerSession
# from ptpython.repl import embed
from pymodbus import Framer, ModbusException
from pymodbus.client import AsyncModbusSerialClient
from util_serial_port import get_serial_port2
from util_modbus_mischventil import Mischventil
from util_modbus_relais import Relais
from util_modbus_adc import Adc

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()
DIRECTORY_MICROPYTHON = (
    DIRECTORY_OF_THIS_FILE.parent.parent / "software-dezentral" / "micropython"
)
assert DIRECTORY_MICROPYTHON.is_dir()
sys.path.append(str(DIRECTORY_MICROPYTHON))

from portable_modbus_registers import EnumModbusRegisters, IregsAll


MODBUS_ADDRESS_RELAIS = 1
MODBUS_ADDRESS_ADC = 2
MODBUS_ADDRESS_BELIMO = 3

TIMEOUT_AFTER_MODBUS_TRANSFER_S = 0.1

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def get_modbus_client():
    port = get_serial_port2()
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


class Context:
    def __init__(self, config_baubaschnitt: config_base.ConfigBauabschnitt):
        self.modbus = get_modbus_client()
        self.config_baubaschnitt = config_baubaschnitt

    async def __aenter__(self):
        await self.modbus.connect()
        return self

    async def __aexit__(self, *exc):
        self.modbus.close()
        return False

    async def modbus_haueser_loop(self) -> None:
        for haus in self.config_baubaschnitt.haeuser:
            await self.handle_haus(haus)
            # await self.handle_haus_relais(haus)

            # await self.reboot_reset(haus=haus)

    async def handle_haus_relais(self, haus: config_base.Haus) -> None:
        try:
            response = await self.modbus.read_holding_registers(
                slave=haus.config_haus.modbus_client_id,
                address=EnumModbusRegisters.SETGET16BIT_RELAIS_GPIO,
                count=1,
            )

        except ModbusException as exc:
            print(f"ERROR: exception in pymodbus {exc}")
            haus.status_haus.modbus_history.failed()
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        assert len(response.registers) == 1
        print(f"SETGET16BIT_RELAIS_GPIO: {response.registers}")
        await asyncio.sleep(0.01)

    async def handle_haus(self, haus: config_base.Haus) -> None:
        iregs_all = IregsAll()
        try:
            response = await self.modbus.read_input_registers(
                slave=haus.config_haus.modbus_client_id,
                address=EnumModbusRegisters.SETGET16BIT_ALL,
                count=iregs_all.register_count,
            )

        except ModbusException as exc:
            print(f"ERROR: exception in pymodbus {exc}")
            haus.status_haus.modbus_history.failed()
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            raise ModbusException("Hallo")

        assert len(response.registers) == iregs_all.register_count
        haus.status_haus.modbus_success_iregs = response
        haus.status_haus.modbus_history.success()
        print(f"Iregsall: {response.registers}")
        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)

    async def reboot_reset(self, haus: config_base.Haus):
        try:
            response = await self.modbus.write_coil(
                slave=haus.config_haus.modbus_client_id,
                address=EnumModbusRegisters.SETGET1BIT_REBOOT_WATCHDOG,
                value=True,
            )
        except ModbusException as exc:
            print(f"ERROR: exception in pymodbus {exc}")
            haus.status_haus.modbus_history.failed()
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        print("Reboot")


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


async def task_modbus():
    async with Context(config_bochs.config_bauabschnitt_bochs) as ctx:
        m = Mischventil(ctx.modbus, MODBUS_ADDRESS_BELIMO)
        r = Relais(ctx.modbus, MODBUS_ADDRESS_RELAIS)
        a = Adc(ctx.modbus, MODBUS_ADDRESS_ADC)
        while True:
            print("")
            await ctx.modbus_haueser_loop()
            haus = ctx.config_baubaschnitt.haeuser[0].status_haus
            print(haus.modbus_history.text_history)
            await asyncio.sleep(0.5)
            # await asyncio.sleep(20.0)

            await a.set_adc()

            if True:
                relative_position = await m.relative_position
                print(f"{relative_position}")
                absolute_power_kW = await m.absolute_power_kW
                print(f"{absolute_power_kW}")

            await r.set(
                list_relays=(True, True, False, False, False, False, False, False)
            )


async def main(port: int = 8222):
    if False:
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
        # await asyncio.Future()  # Wait forever.

    await asyncio.create_task(task_modbus())

    # await interactive_shell()
    await asyncio.Future()  # Wait forever.
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=False)
