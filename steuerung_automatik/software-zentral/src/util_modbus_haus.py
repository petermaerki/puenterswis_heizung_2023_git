import asyncio
import pathlib
import sys

from pymodbus.client import AsyncModbusSerialClient

import config_base

# from ptpython.contrib.asyncssh_repl import ReplSSHServerSession
# from ptpython.repl import embed
from pymodbus import ModbusException

from src.constants import TIMEOUT_AFTER_MODBUS_TRANSFER_S
from src.hsm_dezentral_signal import ModbusSuccess

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()
DIRECTORY_MICROPYTHON = (
    DIRECTORY_OF_THIS_FILE.parent.parent / "software-dezentral" / "micropython"
)
assert DIRECTORY_MICROPYTHON.is_dir()
sys.path.append(str(DIRECTORY_MICROPYTHON))

from portable_modbus_registers import EnumModbusRegisters, IregsAll


class ModbusHaus:
    def __init__(self, modbus: AsyncModbusSerialClient, config_haus: config_base.Haus):
        self._modbus = modbus
        self._config_haus = config_haus

    async def handle_haus_relais(self, haus: config_base.Haus) -> None:
        try:
            response = await self._modbus.read_holding_registers(
                slave=haus.config_haus.modbus_client_id,
                address=EnumModbusRegisters.SETGET16BIT_RELAIS_GPIO,
                count=1,
            )

        except ModbusException as exc:
            print(
                f"ERROR: exception in haus {haus.config_haus.modbus_client_id}: {exc}"
            )
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
            response = await self._modbus.read_input_registers(
                slave=haus.config_haus.modbus_client_id,
                address=EnumModbusRegisters.SETGET16BIT_ALL,
                count=iregs_all.register_count,
            )

        except ModbusException as exc:
            print(
                f"ERROR: exception in haus {haus.config_haus.modbus_client_id}: {exc}"
            )
            haus.status_haus.modbus_history.failed()
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            raise ModbusException("Hallo")

        assert len(response.registers) == iregs_all.register_count
        # haus.status_haus.modbus_success_iregs = response
        # haus.status_haus.modbus_history.success()
        haus.status_haus.hsm_dezentral.dispatch(ModbusSuccess(response.registers))
        print(f"Iregsall: {response.registers}")
        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)

    async def reboot_reset(self, haus: config_base.Haus):
        try:
            response = await self._modbus.write_coil(
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
