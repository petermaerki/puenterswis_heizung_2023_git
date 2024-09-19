import asyncio
from typing import Any, List

from micropython import util_constants
from micropython.portable_modbus_registers import EnumModbusRegisters, IregsAll
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.pdu import ModbusResponse

from zentral import util_modbus_dac, util_modbus_mischventil, util_modbus_relais
from zentral.config_base import MODBUS_OFFSET_HAUS, ConfigEtappe
from zentral.constants import MODBUS_ADDRESS_BELIMO, MODBUS_ADDRESS_DAC, MODBUS_ADDRESS_RELAIS
from zentral.context import Context
from zentral.util_modbus import MODBUS_MAX_REGISTER_START_ADDRESS
from zentral.util_modbus_communication import ModbusCommunication

_DS_COUNT = 8

MOCK_DURATION_S = 0.1


class ModbusMockClient:
    def __init__(self, context: "ContextMock"):
        assert isinstance(context, ContextMock)
        self._context = context

    def validate_modbus_slave_address(self, slave: int) -> None:
        for pcb_dezentral_heizzentrale in self._context.modbus_communication.pcbs_dezentral_heizzentrale.pcbs:
            if pcb_dezentral_heizzentrale.modbus_slave_addr == slave:
                return
        _haus = self._context.config_etappe.get_haus_by_modbus_server_id(modbus_server_id=slave)
        return

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

        self.validate_modbus_slave_address(slave=slave)

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
            self.validate_modbus_slave_address(slave=slave)

            rsp = ModbusResponse()
            rsp.registers = [1]
            return rsp

        if slave == MODBUS_ADDRESS_BELIMO:
            if address == util_modbus_mischventil.EnumRegisters.RELATIVE_POSITION:
                rsp = ModbusResponse()
                rsp.registers = [50]
                return rsp
            if address == util_modbus_mischventil.EnumRegisters.ABSOLUTE_POWER_W:
                rsp = ModbusResponse()
                rsp.registers = [100, 100]
                return rsp
            if address == MODBUS_MAX_REGISTER_START_ADDRESS:
                rsp = ModbusResponse()
                rsp.registers = count * [100]
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

        def assert_modbus():
            if slave == MODBUS_ADDRESS_DAC:
                assert address == util_modbus_dac.Dac.DAC_ADDRESS
                assert len(values) == 8
                return

            if slave > MODBUS_OFFSET_HAUS:
                assert address == EnumModbusRegisters.SETGET16BIT_GPIO
                assert len(values) == 1
                return

        assert_modbus()

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
        assert address in (util_modbus_relais.ModbusRelais.COIL_ADDRESS, EnumModbusRegisters.SETGET16BIT_GPIO)
        assert slave == MODBUS_ADDRESS_RELAIS

        rsp = ModbusResponse()
        rsp.registers = []
        return rsp


class ModbusCommunicationMock(ModbusCommunication):
    def __init__(self, context: Context):
        super().__init__(context=context)

    def _get_modbus_client(self, n: int, baudrate: int) -> AsyncModbusSerialClient:
        return ModbusMockClient(self.context)

    async def connect(self):
        return None


class ContextMock(Context):
    def __init__(self, config_etappe: ConfigEtappe):
        super().__init__(config_etappe=config_etappe)

    def _factory_modbus_communication(self) -> ModbusCommunication:
        return ModbusCommunicationMock(self)
