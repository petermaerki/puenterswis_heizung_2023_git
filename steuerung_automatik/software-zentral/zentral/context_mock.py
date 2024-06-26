import asyncio
from typing import Any, List


from zentral.constants import (
    MODBUS_ADDRESS_DAC,
    MODBUS_ADDRESS_BELIMO,
    MODBUS_ADDRESS_RELAIS,
)
from zentral.config_base import ConfigEtappe, Haus
from pymodbus.pdu import ModbusResponse
from micropython.portable_modbus_registers import EnumModbusRegisters, IregsAll
from micropython import util_constants
from pymodbus.client import AsyncModbusSerialClient
from zentral.util_modbus_communication import ModbusCommunication
from zentral.context import Context

from zentral import util_modbus_mischventil
from zentral import util_modbus_gpio
from zentral import util_modbus_dac


_DS_COUNT = 8

MOCK_DURATION_S = 0.1


class ModbusMockClient:
    def __init__(self, context: "ContextMock"):
        assert isinstance(context, ContextMock)
        self._context = context

    def _get_haus(self, slave: int) -> Haus:
        return self._context.config_etappe.get_haus_by_modbus_server_id(modbus_server_id=slave)

    def close(self):
        pass

    async def read_input_registers(
        self,
        address: int,
        count: int,
        slave: int,
        **kwargs: Any,
    ) -> ModbusResponse:
        assert address == EnumModbusRegisters.SETGET16BIT_ALL_SLOW

        await asyncio.sleep(MOCK_DURATION_S)

        _haus = self._get_haus(slave=slave)

        a = IregsAll()
        registers = [
            0,
        ] * a.register_count
        a.version_hw.set_value(registers, util_constants.VERSION_HW)
        a.version_sw.set_value(registers, util_constants.VERSION_SW)
        a.reset_cause.set_value(registers, 4)
        a.uptime_s.set_value(registers, 42)
        a.errors_modbus.set_value(registers, 42)
        a.relais_gpio.set_value(registers, 1)
        assert a.ds18_temperature_cK.count == _DS_COUNT
        for i in range(_DS_COUNT):
            a.ds18_ok_percent.set_value(registers, 10, i)
            a.ds18_temperature_cK.set_value(registers, 4711, i)

        registers = [10000, 100, 1, 1200, 42, 0, 0, 0, 29359, 29365, 29378, 29346, 29352, 29359, 0, 0, 100, 100, 100, 100, 100, 100]
        rsp = ModbusResponse()
        rsp.registers = registers
        return rsp

    async def read_holding_registers(
        self,
        address: int,
        count: int,
        slave: int,
        **kwargs: Any,
    ) -> ModbusResponse:
        await asyncio.sleep(MOCK_DURATION_S)

        if address == EnumModbusRegisters.SETGET16BIT_GPIO:
            _haus = self._get_haus(slave=slave)

            rsp = ModbusResponse()
            rsp.registers = [1]
            return rsp

        if slave == MODBUS_ADDRESS_BELIMO:
            if address == util_modbus_mischventil.EnumRegisters.RELATIVE_POSITION:
                rsp = ModbusResponse()
                rsp.registers = [50]
                return rsp
            if address == util_modbus_mischventil.EnumRegisters.ABSOLUTE_POWER_kW:
                rsp = ModbusResponse()
                rsp.registers = [100, 100]
                return rsp
        assert False

    async def write_registers(
        self,
        address: int,
        values: List[int],
        slave: int,
        **kwargs: Any,
    ) -> ModbusResponse:
        assert isinstance(values, (list, tuple))
        assert address == util_modbus_dac.Dac.DAC_ADDRESS
        assert slave == MODBUS_ADDRESS_DAC
        assert len(values) == 8

        await asyncio.sleep(MOCK_DURATION_S)

        rsp = ModbusResponse()
        rsp.registers = []
        return rsp

    async def write_coils(
        self,
        address: int,
        values: List[bool],
        slave: int,
        **kwargs: Any,
    ) -> ModbusResponse:
        assert isinstance(values, (list, tuple))
        assert address == util_modbus_gpio.Gpio.COIL_ADDRESS
        assert slave == MODBUS_ADDRESS_RELAIS

        rsp = ModbusResponse()
        rsp.registers = []
        return rsp


class ModbusCommunicationMock(ModbusCommunication):
    def __init__(self, context: Context):
        super().__init__(context=context)

    def _get_modbus_client(self) -> AsyncModbusSerialClient:
        return ModbusMockClient(self._context)

    async def connect(self):
        return None


class ContextMock(Context):
    def __init__(self, config_etappe: ConfigEtappe):
        super().__init__(config_etappe=config_etappe)

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunicationMock(self)
