
import asyncio

from config import raspi_os_config
from micropython.portable_modbus_registers import (IREGS_ALL,
                                                   EnumModbusRegisters)

from zentral import config_etappe
from zentral.constants import ModbusAddressOeokofen, Waveshare_4RS232
from zentral.context import Context
from zentral.util_modbus import get_modbus_client
from zentral.util_modbus_oekofen import Oekofen, OekofenRegisters
from zentral.util_modbus_wrapper import ModbusWrapper


async def main():
    # async with Context(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname)) as context:
    if True:
        context = Context(config_etappe.create_config_etappe(hostname=raspi_os_config.hostname))
        modbus_client = get_modbus_client(n=Waveshare_4RS232.MODBUS_OEKOFEN, baudrate=19200)
        await  modbus_client.connect()
        modbus = ModbusWrapper(context=context, modbus_client=modbus_client)

        if False:
            rsp = await modbus_client.read_input_registers(
                slave=ModbusAddressOeokofen.OEKOFEN,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )

        if True:
            o = Oekofen(modbus=modbus,modbus_address= ModbusAddressOeokofen.OEKOFEN)
            all_registers = await o.all_registers
            modbus_oekofen_registers = OekofenRegisters(registers=all_registers)
            modbus_oekofen_registers.append_to_file()


    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
