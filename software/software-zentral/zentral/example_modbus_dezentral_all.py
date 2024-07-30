
import asyncio
from pymodbus import ModbusException
from zentral.util_modbus import get_modbus_client

from micropython.portable_modbus_registers import  EnumModbusRegisters, IREGS_ALL
from zentral.util_modbus_iregs_all import ModbusIregsAll

MODBUS_SLAVE = 113
async def main():
    modbus = get_modbus_client()
    await modbus.connect()

    while True:
        try:
            rsp = await modbus.read_input_registers(
                slave=MODBUS_SLAVE,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )

        except ModbusException as exc:
            print(f"{MODBUS_SLAVE=}: {exc!r}")
            await asyncio.sleep(1.0)
            return False

        modbus_iregs_all = ModbusIregsAll(rsp.registers)
        # print(modbus_iregs_all.debug2_temperatureC)
        # print(modbus_iregs_all.debug_temperatureC_percent)
        await asyncio.sleep(1.0)


    modbus.close()
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
